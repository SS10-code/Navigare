"""
dashboard.py — Navigare Retail Analytics
Week 5 · Phase 2

Sidebar = navigation (one page at a time, no tab clutter)
Each page has a plain-English explanation before any chart.
All charts are live Plotly. No static images. Works with any input data.

Run:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings, os, json, random
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Navigare · Retail Analytics",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] { background: #0a0e1a; }
[data-testid="stSidebar"] { background: #0d1220; border-right: 1px solid #1e2d4a; }
.main .block-container { padding: 2rem 2.5rem 3rem; max-width: 1300px; }

/* ── Sidebar nav buttons ── */
div[data-testid="stSidebar"] .stButton > button {
    width: 100%; text-align: left; background: transparent;
    border: none; border-radius: 8px; color: #8ba3c7;
    padding: 10px 14px; font-size: 14px; font-weight: 500;
    transition: all 0.15s ease; margin-bottom: 2px;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background: #1a2844; color: #e8f0ff;
}

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.kpi {
    flex: 1; min-width: 140px;
    background: linear-gradient(135deg, #111827, #1a2744);
    border: 1px solid #1e3a5f; border-radius: 12px;
    padding: 18px 20px;
}
.kpi-label { color: #6b8ab0; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
.kpi-value { color: #e8f0ff; font-size: 26px; font-weight: 700; line-height: 1; }
.kpi-sub   { color: #4a6fa5; font-size: 11px; margin-top: 4px; }

/* ── Page header ── */
.page-title { font-size: 22px; font-weight: 700; color: #e8f0ff; margin-bottom: 4px; }
.page-sub   { font-size: 14px; color: #6b8ab0; margin-bottom: 24px; }

/* ── Explanation boxes ── */
.explain {
    background: #0f1e35; border-left: 3px solid #3b6fd4;
    border-radius: 0 8px 8px 0; padding: 14px 18px;
    margin: 0 0 20px; color: #c5d8f0; font-size: 13.5px; line-height: 1.65;
}
.explain b { color: #7fb3ff; }
.explain code { background: #1a2d4a; padding: 1px 6px;
    border-radius: 4px; font-size: 12px; color: #a5d6a7; }
.warn {
    background: #1f1200; border-left: 3px solid #f59e0b;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    margin: 0 0 16px; color: #fcd34d; font-size: 13px;
}
.formula {
    background: #0d1a0d; border: 1px solid #2d5a2d; border-radius: 8px;
    padding: 14px 18px; font-family: monospace; font-size: 13px;
    color: #86efac; margin: 12px 0; line-height: 1.8;
}
.section-label {
    font-size: 11px; font-weight: 700; color: #3b6fd4;
    text-transform: uppercase; letter-spacing: 1.2px;
    margin: 28px 0 10px;
}
.divider { border: none; border-top: 1px solid #1a2d4a; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# plotly dark theme shorthand
PLT = dict(template="plotly_dark", paper_bgcolor="#0a0e1a", plot_bgcolor="#0f1729")
BLUE = "#3b6fd4"; YELLOW = "#f59e0b"; GREEN = "#22c55e"
PURPLE = "#a855f7"; RED = "#ef4444"; CYAN = "#06b6d4"


# ─────────────────────────────────────────────────────────────
# DATA LOADING  (works with any CSV swap)
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_all():
    rng = np.random.default_rng(42); random.seed(42)
    TODAY = datetime.today().date()

    # ── Transactions ──────────────────────────────────────────
    txn_path = "data/clean/unified_transactions.csv"
    if os.path.exists(txn_path):
        txn = pd.read_csv(txn_path, parse_dates=["Transaction_Date"])
        if "Store_Type" not in txn.columns or txn["Store_Type"].isna().all():
            txn["Store_Type"] = txn["Source_Currency"].map(
                {"BRL": "E-Commerce", "GBP": "Brick-and-Mortar"})
        txn["Store_Type"] = txn["Store_Type"].fillna(
            txn["Source_Currency"].map({"BRL":"E-Commerce","GBP":"Brick-and-Mortar"}))
    else:
        cats  = ["Pastries","Breads","Cakes","Drinks","Savory"]
        types = ["E-Commerce","Brick-and-Mortar"]
        base  = datetime.combine(TODAY - timedelta(days=365), datetime.min.time())
        rows  = []
        for i in range(1200):
            st_ = random.choice(types)
            ts  = base + timedelta(days=int(rng.integers(0,364)),
                                   hours=int(rng.integers(8,20)),
                                   minutes=int(rng.integers(0,59)))
            price = round(float(rng.uniform(2.5,35.0)),2)
            qty   = int(rng.integers(1,6))
            rows.append({
                "Store_Type":"E-Commerce" if st_=="E-Commerce" else "Brick-and-Mortar",
                "Transaction_ID":f"TXN-{i:05d}",
                "Customer_ID":f"C{rng.integers(1,61):04d}",
                "Product_ID":int(rng.integers(1,26)),
                "Item_Price_USD":price,"Quantity":qty,
                "Line_Total_USD":round(price*qty,2),
                "Transaction_Date":ts.date(),
                "Category":random.choice(cats),
                "Source_Currency":"BRL" if st_=="E-Commerce" else "GBP",
            })
        txn = pd.DataFrame(rows)
        txn["Transaction_Date"] = pd.to_datetime(txn["Transaction_Date"])

    # ── Daily series (R-04: missing days → 0, not NaN) ────────
    daily = (txn.groupby("Transaction_Date")["Line_Total_USD"]
               .sum().resample("D").sum().fillna(0).reset_index())
    daily.columns = ["Date","Revenue_USD"]
    daily = daily.sort_values("Date").reset_index(drop=True)

    # ── Features ──────────────────────────────────────────────
    feat_path = "data/clean/features.csv"
    feat = pd.read_csv(feat_path, parse_dates=["Date"]) if os.path.exists(feat_path) else None

    # ── Inventory ─────────────────────────────────────────────
    for p in ["data/clean/inventory_clean.csv","data/raw/inventory.csv"]:
        if os.path.exists(p):
            inv = pd.read_csv(p); break
    else:
        inv = None

    # ── EMA forecast ─────────────────────────────────────────
    ema_path = "data/clean/ema_forecast.csv"
    ema = pd.read_csv(ema_path, parse_dates=["Date"]) if os.path.exists(ema_path) else None

    # ── VIF & ADF ────────────────────────────────────────────
    vif = pd.read_csv("data/clean/vif_results.csv") if os.path.exists("data/clean/vif_results.csv") else None
    adf = pd.read_csv("data/clean/adf_results.csv") if os.path.exists("data/clean/adf_results.csv") else None

    # ── Chaos report ─────────────────────────────────────────
    chaos = None
    if os.path.exists("data/clean/chaos_report.json"):
        with open("data/clean/chaos_report.json") as f:
            chaos = json.load(f)

    return txn, daily, feat, inv, ema, vif, adf, chaos


with st.spinner("Loading data..."):
    txn_df, daily_df, feat_df, inv_df, ema_df, vif_df, adf_df, chaos_data = load_all()


# ─────────────────────────────────────────────────────────────
# SIDEBAR  — navigation + global controls
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 20px'>
      <div style='font-size:20px;font-weight:800;color:#e8f0ff;letter-spacing:-0.5px'>🧭 Navigare</div>
      <div style='font-size:11px;color:#4a6fa5;margin-top:2px'>Retail Analytics · Week 5</div>
    </div>
    """, unsafe_allow_html=True)

    pages = {
        "📊  Overview":          "overview",
        "📈  Sales Forecast":    "forecast",
        "🔬  Feature Engineering":"features",
        "📦  Inventory":         "inventory",
        "🐒  Data Quality":      "chaos",
        "🗺️  Schema & Rules":    "schema",
    }

    if "page" not in st.session_state:
        st.session_state.page = "overview"

    for label, key in pages.items():
        active = st.session_state.page == key
        style = "background:#1a2844;color:#e8f0ff;" if active else ""
        if st.button(label, key=f"nav_{key}",
                     use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown("<hr style='border-color:#1a2d4a;margin:20px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;color:#4a6fa5;font-weight:600;text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px'>Global Filters</div>", unsafe_allow_html=True)

    store_opts = ["All Stores"] + sorted(txn_df["Store_Type"].dropna().unique().tolist())
    sel_store  = st.selectbox("Store Type", store_opts, label_visibility="collapsed")

    st.markdown("<div style='font-size:11px;color:#4a6fa5;margin-top:16px;margin-bottom:6px'>Date Range</div>", unsafe_allow_html=True)
    date_min = txn_df["Transaction_Date"].min().date()
    date_max = txn_df["Transaction_Date"].max().date()
    date_range = st.date_input("", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max,
                               label_visibility="collapsed")

    st.markdown("<hr style='border-color:#1a2d4a;margin:20px 0'>", unsafe_allow_html=True)
    total_rev = txn_df["Line_Total_USD"].sum()
    st.markdown(f"<div style='font-size:11px;color:#4a6fa5'>Total Revenue</div><div style='font-size:18px;font-weight:700;color:#22c55e'>${total_rev:,.0f}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:11px;color:#4a6fa5;margin-top:8px'>{date_min} → {date_max}</div>", unsafe_allow_html=True)


# ── Filter data based on sidebar ──────────────────────────────
filt = txn_df.copy()
if sel_store != "All Stores":
    filt = filt[filt["Store_Type"] == sel_store]
if len(date_range) == 2:
    filt = filt[(filt["Transaction_Date"].dt.date >= date_range[0]) &
                (filt["Transaction_Date"].dt.date <= date_range[1])]

daily_filt = (filt.groupby("Transaction_Date")["Line_Total_USD"]
              .sum().resample("D").sum().fillna(0))


# ─────────────────────────────────────────────────────────────
# HELPER: KPI ROW
# ─────────────────────────────────────────────────────────────
def kpi_row(metrics: list):
    """metrics = list of (label, value, sub) tuples"""
    html = '<div class="kpi-row">'
    for label, value, sub in metrics:
        html += f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═════════════════════════════════════════════════════════════
if st.session_state.page == "overview":
    st.markdown('<div class="page-title">📊 Business Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">High-level snapshot of your store\'s performance. Everything here updates when you change the filters in the sidebar.</div>', unsafe_allow_html=True)

    rev   = filt["Line_Total_USD"].sum()
    orders= filt["Transaction_ID"].nunique()
    aov   = filt.groupby("Transaction_ID")["Line_Total_USD"].sum().mean() if orders > 0 else 0
    low   = int(inv_df["Low_Stock_Flag"].sum()) if inv_df is not None and "Low_Stock_Flag" in inv_df.columns else 0
    dead  = int(inv_df["Dead_Stock_Flag"].sum()) if inv_df is not None and "Dead_Stock_Flag" in inv_df.columns else 0

    kpi_row([
        ("Total Revenue",       f"${rev:,.0f}",     f"{sel_store}"),
        ("Total Orders",        f"{orders:,}",       "unique transactions"),
        ("Avg Order Value",     f"${aov:,.2f}",      "per checkout"),
        ("Low Stock SKUs",      f"{low}",            "need restocking"),
        ("Dead Stock SKUs",     f"{dead}",           "not sold in 60+ days"),
    ])

    # Revenue over time
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="section-label">Revenue Over Time</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_filt.index, y=daily_filt.values,
            fill="tozeroy", fillcolor="rgba(59,111,212,0.1)",
            line=dict(color=BLUE, width=2), name="Daily Revenue"))
        # 7-day rolling average
        roll = daily_filt.rolling(7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=roll.index, y=roll.values,
            line=dict(color=YELLOW, width=2, dash="dash"),
            name="7-day avg"))
        fig.update_layout(**PLT, height=340, hovermode="x unified",
            margin=dict(l=0,r=0,t=10,b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_yaxes(title="Revenue (USD)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-label">By Store Type</div>', unsafe_allow_html=True)
        rv = filt.groupby("Store_Type")["Line_Total_USD"].sum().reset_index()
        fig_pie = px.pie(rv, values="Line_Total_USD", names="Store_Type",
            color_discrete_sequence=[BLUE, YELLOW], hole=0.55)
        fig_pie.update_layout(**PLT, height=260, margin=dict(l=0,r=0,t=0,b=0),
            showlegend=True, legend=dict(orientation="h", y=-0.1))
        fig_pie.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Category breakdown
    st.markdown('<div class="section-label">Revenue by Category</div>', unsafe_allow_html=True)
    if "Category" in filt.columns:
        cat = filt.groupby("Category")["Line_Total_USD"].sum().sort_values(ascending=True)
        fig_cat = go.Figure(go.Bar(
            x=cat.values, y=cat.index, orientation="h",
            marker_color=BLUE, text=[f"${v:,.0f}" for v in cat.values],
            textposition="outside"))
        fig_cat.update_layout(**PLT, height=260, margin=dict(l=0,r=0,t=10,b=0))
        fig_cat.update_xaxes(title="Revenue (USD)")
        st.plotly_chart(fig_cat, use_container_width=True)

    # Daily by store
    st.markdown('<div class="section-label">Daily Revenue Split</div>', unsafe_allow_html=True)
    ds2 = txn_df.copy()
    if sel_store != "All Stores":
        ds2 = ds2[ds2["Store_Type"] == sel_store]
    ds2 = ds2.groupby(["Transaction_Date","Store_Type"])["Line_Total_USD"].sum().reset_index()
    fig_a = px.area(ds2, x="Transaction_Date", y="Line_Total_USD", color="Store_Type",
        color_discrete_map={"E-Commerce":BLUE,"Brick-and-Mortar":YELLOW})
    fig_a.update_layout(**PLT, height=280, hovermode="x unified",
        margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_a, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# PAGE: SALES FORECAST
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "forecast":
    st.markdown('<div class="page-title">📈 Sales Forecast</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Three forecasting models running side by side. Tune the controls below and see how each one handles your data differently.</div>', unsafe_allow_html=True)

    # Controls inline
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)
    sma_win  = ctrl1.slider("SMA Window (days)", 3, 30, 7,
                            help="How many past days the SMA averages over")
    ema_win  = ctrl2.slider("EMA Window (days)", 3, 30, 7,
                            help="Larger = smoother but slower to react")
    seas_per = ctrl3.number_input("Seasonal Period", 2, 30, 7,
                                  help="7 = weekly seasonality (standard for retail)")
    fc_days  = ctrl4.slider("Forecast Days", 7, 60, 14)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Model explanations ────────────────────────────────────
    e1, e2, e3 = st.columns(3)
    with e1:
        alpha = 2/(ema_win+1)
        st.markdown(f"""
        <div class="explain">
        <b>Simple Moving Average (SMA)</b><br><br>
        Takes the last <b>{sma_win} days</b> of sales and averages them equally.
        Every day counts the same — yesterday has as much weight as 7 days ago.<br><br>
        <b>Good for:</b> stable products with no trend.<br>
        <b>Weakness:</b> always lags behind sudden changes.
        </div>""", unsafe_allow_html=True)
    with e2:
        st.markdown(f"""
        <div class="explain">
        <b>Exponential Moving Average (EMA)</b><br><br>
        Same idea as SMA but <b>recent days count more</b>.
        Yesterday gets weight <code>α={alpha:.3f}</code>, the day before gets
        <code>α×(1-α)</code>, and so on — exponentially fading.<br><br>
        <b>Formula:</b> <code>EMA = α×today + (1-α)×yesterday's EMA</code><br>
        <b>Good for:</b> trending products. Reacts faster than SMA.
        </div>""", unsafe_allow_html=True)
    with e3:
        st.markdown(f"""
        <div class="explain">
        <b>Holt-Winters (Triple Smoothing)</b><br><br>
        The most powerful of the three. Tracks three things simultaneously:
        <b>level</b> (baseline), <b>trend</b> (up/down direction), and
        <b>seasonality</b> (e.g. weekends always spike).<br><br>
        <b>Good for:</b> retail with clear weekly cycles.<br>
        <b>Seasonal period set to {seas_per} days.</b>
        </div>""", unsafe_allow_html=True)

    # ── Build models ──────────────────────────────────────────
    sma_s = daily_filt.rolling(sma_win, min_periods=1).mean()
    ema_s = daily_filt.ewm(span=ema_win, adjust=False).mean()

    hw_ok = False
    try:
        hw = ExponentialSmoothing(daily_filt, trend="add", seasonal="add",
                                  seasonal_periods=int(seas_per),
                                  initialization_method="estimated").fit(optimized=True)
        hw_fit    = hw.fittedvalues
        fc_idx    = pd.date_range(daily_filt.index[-1]+pd.Timedelta(days=1),
                                  periods=fc_days, freq="D")
        hw_fc     = pd.Series(hw.forecast(fc_days).values, index=fc_idx)
        hw_ok     = True
    except Exception as e:
        hw_err = str(e)

    # ── Main chart ────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_filt.index, y=daily_filt.values,
        name="Actual Sales", line=dict(color="#4a6fa5",width=1), opacity=0.6))
    fig.add_trace(go.Scatter(x=sma_s.index, y=sma_s.values,
        name=f"SMA-{sma_win}", line=dict(color=YELLOW,width=2,dash="dash")))
    fig.add_trace(go.Scatter(x=ema_s.index, y=ema_s.values,
        name=f"EMA-{ema_win} (α={alpha:.2f})", line=dict(color=CYAN,width=2.5)))
    if hw_ok:
        fig.add_trace(go.Scatter(x=hw_fit.index, y=hw_fit.values,
            name="Holt-Winters Fitted", line=dict(color=GREEN,width=2), opacity=0.9))
        fig.add_trace(go.Scatter(x=hw_fc.index, y=hw_fc.values,
            name=f"Forecast (+{fc_days}d)",
            line=dict(color=PURPLE,width=2.5,dash="dot"),
            fill="tozeroy", fillcolor="rgba(168,85,247,0.06)"))
        fig.add_vline(x=daily_filt.index[-1].timestamp() * 1000, line_color="#f59e0b",
                      line_dash="dash", line_width=1,
                      annotation_text="  Today", annotation_font_color="#f59e0b",
                      annotation_font_size=11)
    else:
        st.warning(f"Holt-Winters couldn't fit: {hw_err[:120]}")

    fig.update_layout(**PLT, height=420, hovermode="x unified",
        margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title="Revenue (USD)")
    st.plotly_chart(fig, use_container_width=True)

    # ── EMA 14-day table ──────────────────────────────────────
    if ema_df is not None:
        st.markdown('<div class="section-label">14-Day EMA Forward Projection</div>', unsafe_allow_html=True)
        st.markdown("""<div class="explain">
        This table shows where the EMA model thinks revenue is heading over the next 14 days.
        It's not a guarantee — it's a baseline built from recent momentum.
        The further out you go, the less confident the number.
        </div>""", unsafe_allow_html=True)

        tc1, tc2 = st.columns([2,1])
        with tc1:
            fig_e = go.Figure()
            fig_e.add_trace(go.Scatter(
                x=daily_filt.index[-30:], y=daily_filt.values[-30:],
                name="Last 30 days", line=dict(color=BLUE,width=2)))
            fig_e.add_trace(go.Scatter(
                x=ema_df["Date"], y=ema_df["EMA_Forecast"],
                name="EMA Forecast", line=dict(color=CYAN,width=2.5,dash="dot"),
                fill="tozeroy", fillcolor="rgba(6,182,212,0.07)"))
            fig_e.update_layout(**PLT, height=260, hovermode="x unified",
                margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_e, use_container_width=True)
        with tc2:
            d = ema_df[["Date","Day_Ahead","EMA_Forecast"]].copy()
            d["Date"]         = pd.to_datetime(d["Date"]).dt.strftime("%b %d")
            d["EMA_Forecast"] = d["EMA_Forecast"].apply(lambda x: f"${x:,.2f}")
            d.columns         = ["Date","Day","Forecast"]
            st.dataframe(d, use_container_width=True, height=260)

    # ── Accuracy ──────────────────────────────────────────────
    if hw_ok:
        st.markdown('<div class="section-label">How Accurate Are They? (In-Sample Error)</div>', unsafe_allow_html=True)
        st.markdown("""<div class="explain">
        MAE = average dollar amount each model is off by per day.
        Lower is better. These are measured against <i>historical</i> data the model already saw,
        so think of them as a floor — real future error will be higher.
        </div>""", unsafe_allow_html=True)

        act      = daily_filt.reindex(hw_fit.index).fillna(0)
        hw_mae   = (act - hw_fit).abs().mean()
        sma_al   = sma_s.reindex(daily_filt.index).ffill()
        sma_mae  = (daily_filt - sma_al).abs().mean()
        ema_al   = ema_s.reindex(daily_filt.index)
        ema_mae  = (daily_filt - ema_al).abs().mean()

        ac1,ac2,ac3 = st.columns(3)
        winner = min([("SMA",sma_mae),("EMA",ema_mae),("Holt-Winters",hw_mae)],key=lambda x:x[1])
        for col, name, mae in [(ac1,"SMA",sma_mae),(ac2,"EMA",ema_mae),(ac3,"Holt-Winters",hw_mae)]:
            badge = " 🏆" if name==winner[0] else ""
            col.metric(f"{name} MAE{badge}", f"${mae:.2f}", delta="best" if name==winner[0] else None,
                       delta_color="normal" if name==winner[0] else "off")


# ═════════════════════════════════════════════════════════════
# PAGE: FEATURE ENGINEERING
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "features":
    st.markdown('<div class="page-title">🔬 Feature Engineering</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">This is where raw date/revenue columns get transformed into the signals a machine learning model can actually learn from.</div>', unsafe_allow_html=True)

    if feat_df is None:
        st.warning("Run `python feature_engineering.py` first to generate data/clean/features.csv")
        st.stop()

    # ── Section 1: Normalization ─────────────────────────────
    st.markdown('<div class="section-label">1 · Normalization — Putting Numbers on the Same Scale</div>', unsafe_allow_html=True)

    n1, n2 = st.columns([1,2])
    with n1:
        mu    = feat_df["Revenue_USD"].mean()
        sigma = feat_df["Revenue_USD"].std()
        outs  = (feat_df["Revenue_ZScore"].abs() > 2).sum()
        st.markdown(f"""
        <div class="explain">
        <b>Why normalize?</b><br>
        If one feature is in dollars (0–5000) and another is a day number (1–7),
        a model treats the dollar feature as more important just because it's bigger.
        Normalization fixes that.<br><br>
        <b>Z-Score</b> re-centers everything around 0.
        A value of +2 means "2 standard deviations above average" — that's an unusual day.
        Days beyond ±2σ are flagged as outliers.<br><br>
        <b>Mean:</b> ${mu:,.2f}<br>
        <b>Std Dev (σ):</b> ${sigma:,.2f}<br>
        <b>Outlier days (|z|>2):</b> {outs}<br><br>
        <b>Min-Max</b> squeezes everything into [0, 1].
        Simple, but one extreme spike can compress everything else.
        </div>
        <div class="formula">
        Z = (x − μ) / σ<br>
        MinMax = (x − min) / (max − min)
        </div>""", unsafe_allow_html=True)

    with n2:
        fig_n = make_subplots(rows=2, cols=1,
            subplot_titles=("Z-Score  ·  0-centred, ±2σ outlier bands shown in red",
                            "Min-Max  ·  Every value squeezed between 0 and 1"),
            vertical_spacing=0.14)
        fig_n.add_trace(go.Scatter(x=feat_df["Date"], y=feat_df["Revenue_ZScore"],
            line=dict(color=BLUE,width=1.5), name="Z-Score",
            fill="tozeroy", fillcolor="rgba(59,111,212,0.07)"), row=1, col=1)
        for lvl, col in [(2,RED),(-2,RED),(0,"#334155")]:
            fig_n.add_hline(y=lvl, line_color=col,
                            line_dash="dot" if abs(lvl)==2 else "dash",
                            line_width=1, row=1, col=1)
        fig_n.add_trace(go.Scatter(x=feat_df["Date"], y=feat_df["Revenue_MinMax"],
            line=dict(color=CYAN,width=1.5), name="Min-Max",
            fill="tozeroy", fillcolor="rgba(6,182,212,0.07)"), row=2, col=1)
        fig_n.update_layout(**PLT, height=400, showlegend=False,
            margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig_n, use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Section 2: Cyclic Encoding ───────────────────────────
    st.markdown('<div class="section-label">2 · Geometry of Time — Teaching the Model That Sunday Follows Saturday</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1,2])
    with c1:
        st.markdown("""
        <div class="explain">
        <b>The problem with raw day numbers:</b><br>
        If you give a model Mon=1, Tue=2 … Sun=7, it thinks Sunday (7)
        is far from Monday (1). But they're adjacent on the calendar.<br><br>
        <b>The fix:</b> place each day on a circle using sine and cosine.
        Now every day is equidistant from its neighbours — including
        the Sunday→Monday wrap.<br><br>
        <b>Why both sin AND cos?</b><br>
        On a sine curve alone, two different angles can give the same height
        (e.g. 45° and 135° are identical). Adding cosine gives every day
        a unique (x, y) coordinate pair.<br><br>
        <b>Trade-off:</b> tree models (XGBoost) struggle with this because
        they split on one variable at a time. Neural nets and linear
        models handle cyclic coordinates much better.
        </div>
        <div class="formula">
        sin_dow = sin(2π × day / 7)<br>
        cos_dow = cos(2π × day / 7)
        </div>""", unsafe_allow_html=True)

    with c2:
        dow_c  = feat_df.groupby("day_of_week")[["sin_dow","cos_dow"]].first()
        dlbls  = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        dcols  = [BLUE,"#60a5fa","#93c5fd",YELLOW,"#fcd34d","#f97316",RED]
        theta  = np.linspace(0, 2*np.pi, 200)

        fig_circ = go.Figure()
        fig_circ.add_trace(go.Scatter(x=np.sin(theta), y=np.cos(theta),
            mode="lines", line=dict(color="#1e3a5f",width=1), showlegend=False))
        dow_rev = feat_df.groupby("day_of_week")["Revenue_USD"].mean()
        for i, (dow, row) in enumerate(dow_c.iterrows()):
            avg = dow_rev.get(dow, 0)
            fig_circ.add_trace(go.Scatter(
                x=[row["sin_dow"]], y=[row["cos_dow"]],
                mode="markers+text",
                marker=dict(size=18, color=dcols[i],
                            line=dict(color="#0a0e1a",width=2)),
                text=[f"<b>{dlbls[dow]}</b>"],
                textposition="top center",
                textfont=dict(color=dcols[i],size=11),
                name=f"{dlbls[dow]} (${avg:.0f}/day)",
                showlegend=True))
        fig_circ.update_layout(**PLT, height=400,
            xaxis=dict(range=[-1.6,1.6], title="cos(2π·dow/7)", zeroline=False),
            yaxis=dict(range=[-1.6,1.6], title="sin(2π·dow/7)", zeroline=False),
            title="Day of Week on the Unit Circle",
            margin=dict(l=0,r=0,t=40,b=0),
            legend=dict(font=dict(size=10), x=1.02, y=1))
        st.plotly_chart(fig_circ, use_container_width=True)

    # DOW bar
    dow_rev = feat_df.groupby("day_of_week")["Revenue_USD"].mean()
    fig_dow = go.Figure(go.Bar(
        x=[dlbls[i] for i in dow_rev.index],
        y=dow_rev.values,
        marker_color=["#f97316" if i>=5 else BLUE for i in dow_rev.index],
        text=[f"${v:.0f}" for v in dow_rev.values],
        textposition="outside"))
    fig_dow.update_layout(**PLT, height=260,
        title="Average Daily Revenue by Day  ·  orange = weekend",
        margin=dict(l=0,r=0,t=40,b=0),
        yaxis_title="Avg Revenue (USD)")
    st.plotly_chart(fig_dow, use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Section 3: Lag Features ───────────────────────────────
    st.markdown('<div class="section-label">3 · Lag Features — Giving the Model a Memory</div>', unsafe_allow_html=True)

    l1, l2 = st.columns([1,2])
    with l1:
        lag_max = st.slider("Lags to show", 3, 14, 14)
        st.markdown("""
        <div class="explain">
        <b>The problem:</b><br>
        A machine learning model sees one row at a time.
        It has no idea what yesterday's sales were unless you tell it.<br><br>
        <b>The fix:</b> add "lag" columns — copies of past revenue
        shifted forward in time so the model can see history in each row.<br><br>
        <b>Lag 1</b> = yesterday's sales<br>
        <b>Lag 7</b> = same day last week (captures weekly rhythm)<br>
        <b>Lag 14</b> = two weeks ago<br><br>
        <b>⚠️ Data Leakage Warning:</b><br>
        If you're forecasting 7 days ahead, you <i>cannot</i> use Lag 1–6
        because those future days haven't happened yet when you run the model.
        Safe minimum = Lag 7.
        </div>
        <div class="formula">
        Y_t = f(Y_{t-1}, Y_{t-7}, ...) + ε
        </div>""", unsafe_allow_html=True)

    with l2:
        lag_cols  = [f"lag_{i}" for i in range(1, lag_max+1)]
        corr_vals = [feat_df["Revenue_USD"].corr(feat_df[c]) for c in lag_cols]
        best      = max(range(len(corr_vals)), key=lambda i: abs(corr_vals[i]))

        fig_lag = go.Figure(go.Bar(
            x=[f"Lag {i}" for i in range(1, lag_max+1)],
            y=corr_vals,
            marker_color=[GREEN if i==best else (BLUE if v>=0 else RED)
                          for i,v in enumerate(corr_vals)],
            text=[f"{v:.3f}" for v in corr_vals],
            textposition="outside"))
        fig_lag.add_hline(y=0, line_color="#334155", line_width=1)
        fig_lag.update_layout(**PLT, height=320,
            title=f"Correlation with Today's Revenue  ·  Lag {best+1} is strongest ({corr_vals[best]:.3f})",
            yaxis_title="Pearson r", margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_lag, use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Section 4: Stationarity ───────────────────────────────
    st.markdown('<div class="section-label">4 · Stationarity — Making the Time Series Predictable</div>', unsafe_allow_html=True)

    s1, s2 = st.columns([1,2])
    with s1:
        st.markdown("""
        <div class="explain">
        <b>What is stationarity?</b><br>
        A time series is stationary when its average and variance
        stay constant over time — no long upward or downward drift.<br><br>
        Models like ARIMA <i>require</i> stationarity to work properly.
        If revenue is trending up, the model gets confused.<br><br>
        <b>The fix — First-Order Differencing:</b><br>
        Instead of predicting raw revenue, predict the <i>change</i>
        from yesterday. Changes bounce around zero, so the
        model stays calibrated even as the business grows.<br><br>
        The ADF test checks if stationarity is achieved.
        p &lt; 0.05 = stationary ✅
        </div>
        <div class="formula">
        ΔY_t = Y_t − Y_{t-1}<br><br>
        (predict the change, not the level)
        </div>""", unsafe_allow_html=True)
        if adf_df is not None:
            for _, row in adf_df.iterrows():
                ok = "YES" in row.get("Stationary","")
                st.metric(row["Series"],
                          f"p = {row['p_value']:.4f}",
                          delta="✅ Stationary" if ok else "⚠️ Not Stationary",
                          delta_color="normal" if ok else "inverse")

    with s2:
        fig_diff = make_subplots(rows=2, cols=1,
            subplot_titles=("Raw Revenue  ·  may drift upward over time",
                            "After Differencing  ·  changes bounce around zero"),
            vertical_spacing=0.14)
        fig_diff.add_trace(go.Scatter(x=feat_df["Date"], y=feat_df["Revenue_USD"],
            line=dict(color=BLUE,width=1.5), name="Raw",
            fill="tozeroy", fillcolor="rgba(59,111,212,0.07)"), row=1, col=1)
        fig_diff.add_trace(go.Scatter(x=feat_df["Date"], y=feat_df["revenue_diff1"],
            line=dict(color=YELLOW,width=1.5), name="Diff1",
            fill="tozeroy", fillcolor="rgba(245,158,11,0.07)"), row=2, col=1)
        fig_diff.add_hline(y=0, line_color="#334155", line_dash="dash", row=2, col=1)
        fig_diff.update_layout(**PLT, height=400, showlegend=False,
            margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig_diff, use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Section 5: VIF ───────────────────────────────────────
    st.markdown('<div class="section-label">5 · VIF — Checking for Redundant Features</div>', unsafe_allow_html=True)

    v1, v2 = st.columns([1,2])
    with v1:
        st.markdown("""
        <div class="explain">
        <b>What is VIF?</b><br>
        VIF (Variance Inflation Factor) tells you when two features
        are basically saying the same thing.<br><br>
        If <code>rolling_mean_7</code> and <code>lag_7</code>
        are both in your model, they're both describing last week's average.
        The model can't tell which one to trust.<br><br>
        <b>VIF = 1</b> → feature is independent, keep it<br>
        <b>VIF 1–5</b> → some overlap, usually fine<br>
        <b>VIF &gt; 10</b> → too redundant, drop it or use PCA<br><br>
        The rolling features are expected to be HIGH because they're
        just smoothed versions of the lag features.
        Drop them before building XGBoost in Week 9.
        </div>""", unsafe_allow_html=True)

    with v2:
        if vif_df is not None:
            fig_vif = go.Figure(go.Bar(
                x=vif_df["VIF"], y=vif_df["Feature"], orientation="h",
                marker_color=["#ef4444" if v>10 else ("#f59e0b" if v>5 else "#22c55e")
                              for v in vif_df["VIF"]],
                text=[f"{v:.1f}" for v in vif_df["VIF"]],
                textposition="outside"))
            fig_vif.add_vline(x=5,  line_color=YELLOW, line_dash="dot", line_width=1,
                              annotation_text="5 — caution", annotation_font_color=YELLOW, annotation_font_size=10)
            fig_vif.add_vline(x=10, line_color=RED, line_dash="dot", line_width=1,
                              annotation_text="10 — drop", annotation_font_color=RED, annotation_font_size=10)
            fig_vif.update_layout(**PLT, height=380,
                title="VIF by Feature  ·  green=keep, yellow=watch, red=drop",
                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_vif, use_container_width=True)
        else:
            st.info("Run `python feature_engineering.py` to generate VIF results")


# ═════════════════════════════════════════════════════════════
# PAGE: INVENTORY
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "inventory":
    st.markdown('<div class="page-title">📦 Inventory Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Track which products need restocking and which ones are sitting unsold. Low stock = under your reorder threshold. Dead stock = not sold in 60+ days.</div>', unsafe_allow_html=True)

    if inv_df is None:
        st.warning("Run `python generate_mock_data.py` then `python chaos_monkey.py`")
        st.stop()

    low  = int(inv_df["Low_Stock_Flag"].sum())  if "Low_Stock_Flag"  in inv_df.columns else 0
    dead = int(inv_df["Dead_Stock_Flag"].sum()) if "Dead_Stock_Flag" in inv_df.columns else 0
    ok   = len(inv_df) - low - dead

    kpi_row([
        ("Total SKUs",    f"{len(inv_df)}",  "unique products"),
        ("OK Stock",      f"{ok}",            "healthy levels"),
        ("Low Stock ⚠️",  f"{low}",           "below reorder point"),
        ("Dead Stock 💀", f"{dead}",          "no sales in 60+ days"),
    ])

    i1, i2 = st.columns(2)
    with i1:
        st.markdown('<div class="section-label">Stock Health</div>', unsafe_allow_html=True)
        fig_s = go.Figure(go.Bar(
            x=["✅ OK","⚠️ Low","💀 Dead"],
            y=[ok, low, dead],
            marker_color=[GREEN, YELLOW, RED],
            text=[ok, low, dead], textposition="outside"))
        fig_s.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_s, use_container_width=True)

    with i2:
        if "Margin_Pct" in inv_df.columns and "Category" in inv_df.columns:
            st.markdown('<div class="section-label">Margin by Category</div>', unsafe_allow_html=True)
            mg = inv_df.groupby("Category")["Margin_Pct"].mean().sort_values()
            fig_m = go.Figure(go.Bar(
                x=mg.values, y=mg.index, orientation="h",
                marker_color=[GREEN if v>40 else (YELLOW if v>25 else RED) for v in mg.values],
                text=[f"{v:.1f}%" for v in mg.values], textposition="outside"))
            fig_m.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_m, use_container_width=True)

    st.markdown('<div class="section-label">Full Inventory Table</div>', unsafe_allow_html=True)
    disp_cols = [c for c in ["Product_ID","Product_Name","Category","Current_Stock",
                              "Reorder_Level","Cost_Price","Retail_Price","Margin_Pct",
                              "Low_Stock_Flag","Dead_Stock_Flag","Last_Sold_Date"]
                 if c in inv_df.columns]

    def color_flags(val):
        if val == 1: return "background-color:#4a1010;color:#fca5a5"
        return ""

    flag_cols = [c for c in ["Low_Stock_Flag","Dead_Stock_Flag"] if c in inv_df.columns]
    styled = inv_df[disp_cols].style.applymap(color_flags, subset=flag_cols)
    st.dataframe(styled, use_container_width=True, height=380)


# ═════════════════════════════════════════════════════════════
# PAGE: DATA QUALITY (CHAOS MONKEY)
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "chaos":
    st.markdown('<div class="page-title">🐒 Data Quality — Chaos Monkey</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Real retail data is messy. We deliberately break our own data to make sure the pipeline can survive it.</div>', unsafe_allow_html=True)

    st.markdown("""<div class="explain">
    <b>What is Chaos Monkey?</b><br>
    Real-world data has typos, broken sensors, duplicate records, and clock errors.
    Rather than hoping our pipeline handles them, we <i>intentionally inject</i> these
    problems at a 2% rate, then run the cleaner and verify everything gets fixed.<br><br>
    If the cleaner passes, we know the pipeline is resilient to these exact failure modes
    in production. If it fails, we find out now — not when the store owner is looking at the dashboard.
    </div>""", unsafe_allow_html=True)

    if chaos_data is None:
        st.warning("Run `python chaos_monkey.py` to generate the data quality report")
        st.stop()

    passed = chaos_data.get("pipeline_passed", False)
    if passed:
        st.success("✅ Pipeline test PASSED — all injected errors were caught and cleaned")
    else:
        st.error("❌ Pipeline test FAILED — some errors were not cleaned correctly")

    kpi_row([
        ("Original Rows",   str(chaos_data["original_rows"]),  "clean inventory"),
        ("After Corruption", str(chaos_data["corrupted_rows"]), "errors injected"),
        ("After Cleaning",   str(chaos_data["clean_rows"]),     "should match original"),
        ("Pipeline",         "✅ PASSED" if passed else "❌ FAILED", "resilience test"),
    ])

    st.markdown('<div class="section-label">What Was Injected</div>', unsafe_allow_html=True)

    inject_labels = {
        "A1_negative_stock":  ("Negative Stock",      "Scanner logged a return before the original sale was recorded. Result: Current_Stock = -5"),
        "A2_null_price":      ("Missing Price",        "CSV column alignment failure — the price cell mapped to the wrong column during import"),
        "A3_price_inversion": ("Price Below Cost",     "Manual markdown error — someone set the retail price lower than what it costs to make"),
        "A4_future_date":     ("Future Sell Date",     "POS terminal clock was wrong. The last-sold date was stamped in the future"),
        "A5_stock_outlier":   ("Stock = 99,999",       "ERP database migration defaulted missing stock values to the maximum integer"),
        "A6_duplicate_rows":  ("Duplicate Records",    "ETL pipeline ran twice (cron overlap) — same record inserted into the database twice"),
        "A7_blank_name":      ("Blank Product Name",   "Operator pressed Enter without typing the product name during POS setup"),
    }

    clean_labels = {
        "C01_negative_stock":  "Clamped to 0 — can't have negative physical stock",
        "C02_null_price":      "Filled with the median price for that category",
        "C03_price_inversion": "Set to cost × 1.5 minimum margin floor",
        "C04_future_dates":    "Clamped to today's date",
        "C05_stock_outlier":   "Capped at the 99th percentile of original data",
        "C06_duplicates":      "Kept first occurrence, dropped the duplicate",
        "C07_blank_names":     "Filled with UNKNOWN_{Product_ID}",
    }

    inj = chaos_data.get("injection_log", {})
    cln = chaos_data.get("cleaning_report", {})

    for (a_key, (a_name, a_desc)), (c_key, c_desc) in zip(inject_labels.items(), clean_labels.items()):
        with st.expander(f"💉 {a_name}  →  🧹 Fixed"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**What was injected:** {a_desc}")
                rows = inj.get(a_key, {}).get("rows", inj.get(a_key, {}).get("source_rows", []))
                st.markdown(f"Affected rows: `{rows}`")
            with col_b:
                st.markdown(f"**How it was fixed:** {c_desc}")
                fixed = cln.get(c_key, 0)
                st.markdown(f"Rows fixed: **{fixed}**")


# ═════════════════════════════════════════════════════════════
# PAGE: SCHEMA & RULES
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "schema":
    st.markdown('<div class="page-title">🗺️ Schema & Data Rules</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">The mapping contract that turns two messy datasets (Olist from Brazil, UCI from the UK) into one clean unified table in USD.</div>', unsafe_allow_html=True)

    st.markdown("""<div class="explain">
    <b>Why do we need a schema contract?</b><br>
    Olist calls their transaction ID <code>order_id</code>. UCI calls it <code>Invoice</code>.
    Olist prices are in Brazilian Reais (BRL). UCI prices are in British Pounds (GBP).
    Before any analysis can happen, both datasets need to speak the same language.
    This table is that translation dictionary.
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-label">Column Mapping</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Our Column":       ["Store_Type","Transaction_ID","Customer_ID","Product_ID",
                             "Item_Price_USD","Quantity","Line_Total_USD",
                             "Transaction_Date","Category","Source_Currency"],
        "Olist (Brazil)":   ["→ 'E-Commerce'","order_id","customer_id","product_id",
                             "price × 0.20 (BRL→USD)","order_item_id",
                             "price×0.20×qty","order_purchase_timestamp",
                             "product_category_name","BRL"],
        "UCI (UK)":         ["→ 'Brick-and-Mortar'","Invoice","Customer ID","StockCode",
                             "Price × 1.27 (GBP→USD)","Quantity (negatives dropped)",
                             "Price×1.27×Qty","InvoiceDate","Description","GBP"],
        "Why it matters":   ["Lets us filter/split by channel",
                             "Primary key — uniquely identifies each sale",
                             "Links to loyalty program",
                             "Links to inventory table",
                             "Standardized currency for all math",
                             "Negative = return, excluded from sales",
                             "The actual revenue number",
                             "Required for time-series forecasting",
                             "Enables category-level analysis",
                             "Audit trail for FX conversion"],
    }), use_container_width=True, height=360)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Edge-Case Filtering Rules</div>', unsafe_allow_html=True)
    st.markdown("""<div class="explain">
    These rules run every time the pipeline processes new data.
    They're the answer to "what do we do when the data isn't perfect?"
    </div>""", unsafe_allow_html=True)

    rules_data = [
        ("R-01","Negative Quantity","DROP the row",
         "UCI data uses negative qty to represent product returns. Returns aren't sales — they'd deflate revenue numbers."),
        ("R-02","Missing Price","FILL with category median",
         "Can't compute revenue without a price. Use the median price of that product category as a reasonable estimate."),
        ("R-03","Missing Date","DROP the row",
         "A transaction with no date can't be placed on the time-series chart. It would break the forecast."),
        ("R-04","Missing Day in Series","FILL with $0",
         "After grouping by day, some days may have no sales (store closed, holiday). Fill with 0 — not NaN. NaN breaks the rolling average and Holt-Winters."),
        ("R-05","Currency Conversion","BRL×0.20 → USD  |  GBP×1.27 → USD",
         "All revenue must be in the same currency before comparing or summing across stores."),
        ("R-06","Duplicate Records","KEEP first, DROP the rest",
         "If the same Transaction_ID + Product_ID pair appears twice, it means the ETL pipeline ran twice. Keep one copy."),
    ]

    for r_id, trigger, action, reason in rules_data:
        with st.expander(f"**{r_id}** — {trigger}  →  {action}"):
            st.markdown(f"**Why:** {reason}")
            st.code(f"# {r_id}: {trigger}\n# Action: {action}", language="python")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Exchange Rates Used</div>', unsafe_allow_html=True)
    st.markdown("""<div class="explain">
    These are static rates for the prototype. In Week 7, we can wire a live FX API
    (like <code>forex-python</code>) so the rates update automatically.
    </div>""", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Currency Pair": ["BRL → USD", "GBP → USD"],
        "Rate":          ["× 0.20", "× 1.27"],
        "Source":        ["Static (prototype)", "Static (prototype)"],
        "Week 7 plan":   ["forex-python live API", "forex-python live API"],
    }), use_container_width=True)


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top:48px;padding-top:16px;border-top:1px solid #1a2d4a;
            color:#2d4a6a;font-size:11px;text-align:center'>
  🧭 Navigare · Retail Analytics · Week 5 · Phase 2 · github.com/SS10-code/Navigare
</div>
""", unsafe_allow_html=True)