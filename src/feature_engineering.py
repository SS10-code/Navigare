"""
feature_engineering.py
────────────────────────────────────────────────────────────────
Week 5 — Full Feature Engineering Pipeline

Builds every feature the dashboard needs:
  1. EMA  — Exponential Moving Average + 14-day forecast
  2. Z-Score & Min-Max normalization
  3. Cyclical time encoding  (sin/cos DOW, month, WOY)
  4. Lag features            (lag_1 → lag_14)
  5. First-order differencing
  6. Rolling stats
  7. ADF stationarity test
  8. VIF multicollinearity check

All charts are rendered live in dashboard.py via Plotly.
No static image files are generated here.

Output:
    data/clean/features.csv
    data/clean/ema_forecast.csv
    data/clean/vif_results.csv
    data/clean/adf_results.csv

Run:
    python feature_engineering.py
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings, os
warnings.filterwarnings("ignore")

os.makedirs("data/clean", exist_ok=True)

UNIFIED_PATH  = "data/clean/unified_transactions.csv"
FEATURES_PATH = "data/clean/features.csv"
EMA_PATH      = "data/clean/ema_forecast.csv"
VIF_PATH      = "data/clean/vif_results.csv"
ADF_PATH      = "data/clean/adf_results.csv"


def load_daily() -> pd.DataFrame:
    if not os.path.exists(UNIFIED_PATH):
        raise FileNotFoundError(f"{UNIFIED_PATH} not found — run schema_mapper.py first")
    raw = pd.read_csv(UNIFIED_PATH, parse_dates=["Transaction_Date"])
    # Fix Store_Type if null (legacy data)
    if raw["Store_Type"].isna().any():
        raw["Store_Type"] = raw["Source_Currency"].map(
            {"BRL": "E-Commerce", "GBP": "Brick-and-Mortar"})
    # R-04: daily resample, missing days → 0
    daily = (raw.groupby("Transaction_Date")["Line_Total_USD"]
               .sum().resample("D").sum().fillna(0).reset_index())
    daily.columns = ["Date", "Revenue_USD"]
    daily = daily.sort_values("Date").reset_index(drop=True)
    print(f"  Daily rows : {len(daily)}")
    print(f"  Date range : {daily['Date'].min().date()} → {daily['Date'].max().date()}")
    print(f"  Zero-rev days (R-04 padded) : {(daily['Revenue_USD']==0).sum()}")
    return daily


# ═══════════════════════════════════════════════════════════════
# 1. EMA
# ═══════════════════════════════════════════════════════════════

def add_ema(daily: pd.DataFrame) -> pd.DataFrame:
    """
    EMA formula:  EMA_t = α × y_t  +  (1−α) × EMA_{t-1}
    α = 2 / (N + 1)

    Recent days weighted exponentially more than older days.
    vs SMA: SMA weights every day in window equally → more lag.
    """
    for span in [7, 14, 30]:
        daily[f"EMA_{span}"] = daily["Revenue_USD"].ewm(span=span, adjust=False).mean()
    print(f"  EMA_7, EMA_14, EMA_30 added")
    return daily


def build_ema_forecast(daily: pd.DataFrame, span: int = 14) -> pd.DataFrame:
    """
    14-day forward EMA projection.
    Bootstraps from last EMA value using same alpha decay.
    """
    alpha     = 2 / (span + 1)
    last_rev  = daily["Revenue_USD"].iloc[-1]
    last_ema  = daily[f"EMA_{span}"].iloc[-1]
    last_date = daily["Date"].iloc[-1]

    rows, ema_carry = [], last_ema
    for i in range(1, 15):
        ema_carry = alpha * last_rev + (1 - alpha) * ema_carry
        rows.append({
            "Date":         last_date + pd.Timedelta(days=i),
            "Day_Ahead":    i,
            "EMA_Forecast": round(ema_carry, 2),
            "Alpha":        round(alpha, 4),
            "Span":         span,
        })
    df = pd.DataFrame(rows)
    df.to_csv(EMA_PATH, index=False)
    print(f"  14-day EMA forecast saved → {EMA_PATH}")
    return df


# ═══════════════════════════════════════════════════════════════
# 2. NORMALIZATION
# ═══════════════════════════════════════════════════════════════

def add_normalization(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Z-Score  : z = (x − μ) / σ
      → re-centers at mean=0, std=1
      → each unit = 1 standard deviation from mean
      → use when: roughly normal distribution, outlier detection

    Min-Max  : x' = (x − x_min) / (x_max − x_min)
      → squeezes every point into [0, 1]
      → use when: bounded input needed (NN sigmoid/softmax)
      → weakness: one extreme outlier compresses all other values
    """
    mu    = daily["Revenue_USD"].mean()
    sigma = daily["Revenue_USD"].std()
    x_min = daily["Revenue_USD"].min()
    x_max = daily["Revenue_USD"].max()

    daily["Revenue_ZScore"] = ((daily["Revenue_USD"] - mu) / sigma).round(4)
    daily["Revenue_MinMax"] = ((daily["Revenue_USD"] - x_min) / (x_max - x_min)).round(4)

    print(f"  Normalization: μ=${mu:.2f}  σ=${sigma:.2f}  "
          f"outliers(|z|>2)={(daily['Revenue_ZScore'].abs()>2).sum()}")
    return daily


# ═══════════════════════════════════════════════════════════════
# 3. CYCLICAL TIME ENCODING
# ═══════════════════════════════════════════════════════════════

def add_cyclical(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Problem: raw integers (Mon=0 … Sun=6) tell the model Sunday is "far"
    from Monday. Linear distance 6, but they're adjacent on the calendar.

    Solution: project onto unit circle via sin + cos.
      sin_dow = sin(2π × day_of_week / 7)
      cos_dow = cos(2π × day_of_week / 7)

    Why BOTH sin AND cos?
      sin alone: 45° and 135° give identical values → two different days,
                 same number → ambiguous.
      Together:  every point on circle has a unique (sin, cos) pair.

    Trade-off: tree models (XGBoost) split on single variables so they
    struggle to reconstruct the circle. Linear models and NNs handle
    cyclic coordinates much better.
    """
    daily["day_of_week"]   = daily["Date"].dt.dayofweek         # 0=Mon 6=Sun
    daily["sin_dow"]       = np.sin(2*np.pi * daily["day_of_week"] / 7).round(6)
    daily["cos_dow"]       = np.cos(2*np.pi * daily["day_of_week"] / 7).round(6)

    daily["month"]         = daily["Date"].dt.month
    daily["sin_month"]     = np.sin(2*np.pi * daily["month"] / 12).round(6)
    daily["cos_month"]     = np.cos(2*np.pi * daily["month"] / 12).round(6)

    daily["week_of_year"]  = daily["Date"].dt.isocalendar().week.astype(int)
    daily["sin_woy"]       = np.sin(2*np.pi * daily["week_of_year"] / 52).round(6)
    daily["cos_woy"]       = np.cos(2*np.pi * daily["week_of_year"] / 52).round(6)

    daily["is_weekend"]    = (daily["day_of_week"] >= 5).astype(int)
    daily["is_month_end"]  = daily["Date"].dt.is_month_end.astype(int)
    daily["is_month_start"]= daily["Date"].dt.is_month_start.astype(int)

    print(f"  Cyclical encoding added: sin/cos DOW, month, WOY + binary flags")
    return daily


# ═══════════════════════════════════════════════════════════════
# 4. LAG FEATURES
# ═══════════════════════════════════════════════════════════════

def add_lags(daily: pd.DataFrame) -> pd.DataFrame:
    """
    ML models have no memory. Lags convert the temporal sequence
    into spatial features the model can read in a single row.

    Physical intuition (inertia): the best predictor of today's
    revenue is almost always what happened yesterday or exactly
    one cycle ago.

    DATA LEAKAGE WARNING:
    For a 7-day-ahead deployment, you CANNOT use lag_1 → lag_6
    because those rows won't exist yet at inference time.
    Minimum safe lag for 7-day-ahead forecast = lag_7.
    """
    for i in range(1, 15):
        daily[f"lag_{i}"] = daily["Revenue_USD"].shift(i)

    daily["rolling_mean_7"]  = daily["Revenue_USD"].rolling(7,  min_periods=1).mean()
    daily["rolling_std_7"]   = daily["Revenue_USD"].rolling(7,  min_periods=1).std().fillna(0)
    daily["rolling_mean_14"] = daily["Revenue_USD"].rolling(14, min_periods=1).mean()
    daily["rolling_std_14"]  = daily["Revenue_USD"].rolling(14, min_periods=1).std().fillna(0)

    print(f"  Lag features added: lag_1 → lag_14 + rolling mean/std (7, 14)")
    return daily


# ═══════════════════════════════════════════════════════════════
# 5. DIFFERENCING
# ═══════════════════════════════════════════════════════════════

def add_differencing(daily: pd.DataFrame) -> pd.DataFrame:
    """
    First-order differencing: Δy_t = y_t − y_{t−1}

    Why: ARIMA/SARIMAX require stationary series (constant mean + variance).
    Raw revenue may trend upward. Differencing removes the trend by
    making the model predict CHANGE from yesterday instead of the level.
    Changes stay bounded around 0, so the model generalises to future growth.

    Seasonal differencing (diff_7): removes weekly pattern
    Δ7_y_t = y_t − y_{t−7}
    """
    daily["revenue_diff1"] = daily["Revenue_USD"].diff(1).fillna(0)
    daily["revenue_diff7"] = daily["Revenue_USD"].diff(7).fillna(0)
    print(f"  Differencing added: revenue_diff1, revenue_diff7")
    return daily


# ═══════════════════════════════════════════════════════════════
# 6. ADF STATIONARITY TEST
# ═══════════════════════════════════════════════════════════════

def run_adf(daily: pd.DataFrame) -> pd.DataFrame:
    results = []
    for col, label in [
        ("Revenue_USD",    "Raw Revenue"),
        ("revenue_diff1",  "First-Order Diff"),
        ("revenue_diff7",  "Seasonal Diff (7)"),
    ]:
        series = daily[col].dropna()
        stat, pval, _, _, crit, _ = adfuller(series)
        results.append({
            "Series":       label,
            "ADF_Stat":     round(stat, 4),
            "p_value":      round(pval, 6),
            "Stationary":   "✅ YES" if pval < 0.05 else "⚠️ NO",
            "Critical_1pct":round(crit["1%"], 4),
            "Critical_5pct":round(crit["5%"], 4),
        })
        status = "✅ STATIONARY" if pval < 0.05 else "⚠️ NOT STATIONARY"
        print(f"  ADF {label:25s}: p={pval:.6f}  {status}")

    df = pd.DataFrame(results)
    df.to_csv(ADF_PATH, index=False)
    print(f"  ADF results saved → {ADF_PATH}")
    return df


# ═══════════════════════════════════════════════════════════════
# 7. VIF
# ═══════════════════════════════════════════════════════════════

def run_vif(daily_full: pd.DataFrame) -> pd.DataFrame:
    """
    VIF = 1 / (1 − R²_j)
    Measures how much a feature's variance is explained by other features.

    VIF = 1      → no collinearity
    VIF 1–5      → acceptable
    VIF 5–10     → moderate concern
    VIF > 10     → HIGH — drop feature or apply PCA

    Expected: rolling_mean_7 and lag features will show HIGH VIF
    because rolling mean is just a smoothed average of lagged values.
    Recommendation: drop rolling features before XGBoost (Week 9).
    """
    features = ["lag_1","lag_7","lag_14",
                "sin_dow","cos_dow","sin_month","cos_month",
                "is_weekend","rolling_mean_7","rolling_std_7"]

    X = daily_full[features].dropna().copy()
    X += np.random.default_rng(0).normal(0, 1e-9, X.shape)  # tiny jitter to avoid singular matrix

    vif_vals = [variance_inflation_factor(X.values, i) for i in range(len(features))]
    df = pd.DataFrame({
        "Feature": features,
        "VIF":     [round(v, 2) for v in vif_vals],
        "Status":  ["✅ OK" if v < 5 else ("⚠️ Moderate" if v < 10 else "❌ HIGH — consider drop/PCA")
                    for v in vif_vals],
    }).sort_values("VIF", ascending=False).reset_index(drop=True)

    df.to_csv(VIF_PATH, index=False)
    print(f"\n  VIF Results:")
    print(df.to_string(index=False))
    print(f"\n  VIF saved → {VIF_PATH}")
    return df


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🔬  Feature Engineering — Week 5")
    print("=" * 50)

    daily = load_daily()
    daily = add_ema(daily)
    daily = add_normalization(daily)
    daily = add_cyclical(daily)
    daily = add_lags(daily)
    daily = add_differencing(daily)

    # Build EMA 14-day forecast before dropping NaN rows
    ema_fc = build_ema_forecast(daily, span=14)

    # Drop NaN rows introduced by lag shifting (first 14 rows)
    daily_full = daily.dropna().reset_index(drop=True)
    print(f"\n  Rows after NaN drop : {len(daily_full)}  (lost first 14 for lag alignment)")

    # ADF + VIF on full dataset
    print("\n── ADF Stationarity Tests ──")
    adf_df = run_adf(daily_full)

    print("\n── VIF Multicollinearity ──")
    vif_df = run_vif(daily_full)

    # Save full feature matrix
    daily_full.to_csv(FEATURES_PATH, index=False)
    print(f"\n✅  Feature matrix → {FEATURES_PATH}")
    print(f"    Shape : {daily_full.shape[0]} rows × {daily_full.shape[1]} columns")
    print(f"    Cols  : {daily_full.columns.tolist()}\n")