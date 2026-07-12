"""
chaos_monkey.py
────────────────────────────────────────────────────────────────
Week 4 — Data Quality Engineering

Injects 7 real-world anomaly types at 2% rate, then runs the
cleaning pipeline to prove resilience.

Input  → data/raw/inventory.csv
Output → data/raw/inventory_corrupted.csv
         data/clean/inventory_clean.csv
         data/clean/chaos_report.json

Run:
    python chaos_monkey.py
"""

import pandas as pd
import numpy as np
import random, os, json
from datetime import datetime, timedelta

rng   = np.random.default_rng(99)
random.seed(99)
TODAY = datetime.today().date()

os.makedirs("data/raw",   exist_ok=True)
os.makedirs("data/clean", exist_ok=True)

INVENTORY_PATH = "data/raw/inventory.csv"
CORRUPTED_PATH = "data/raw/inventory_corrupted.csv"
CLEAN_PATH     = "data/clean/inventory_clean.csv"
REPORT_PATH    = "data/clean/chaos_report.json"


# ═══════════════════════════════════════════════════════════════
# INJECT
# ═══════════════════════════════════════════════════════════════

def inject(df: pd.DataFrame, rate: float = 0.02):
    dirty = df.copy()
    n     = len(dirty)
    k     = max(1, int(n * rate))
    log   = {}

    print(f"\n🐒  Chaos Monkey  |  {n} rows  |  {k} rows per anomaly type  |  rate={rate*100:.0f}%")
    print("─" * 60)

    # A1 — Negative stock (scanner logged return before sale)
    idx = rng.choice(n, size=k, replace=False).tolist()
    dirty.loc[idx, "Current_Stock"] = -5
    log["A1_negative_stock"] = {"rows": idx, "cause": "Scanner return posted before original sale"}
    print(f"  💉 A1 Negative Stock     → {idx}")

    # A2 — Null price (CSV column misalignment)
    idx = rng.choice(n, size=k, replace=False).tolist()
    dirty.loc[idx, "Retail_Price"] = np.nan
    log["A2_null_price"] = {"rows": idx, "cause": "CSV import lost column alignment"}
    print(f"  💉 A2 Null Price         → {idx}")

    # A3 — Price inversion (retail < cost)
    idx = rng.choice(n, size=k, replace=False).tolist()
    for i in idx:
        dirty.loc[i, "Retail_Price"] = round(dirty.loc[i, "Cost_Price"] * 0.5, 2)
    log["A3_price_inversion"] = {"rows": idx, "cause": "Manual markdown set retail below cost"}
    print(f"  💉 A3 Price Inversion    → {idx}")

    # A4 — Future date (POS clock drift)
    idx = rng.choice(n, size=k, replace=False).tolist()
    future = (TODAY + timedelta(days=int(rng.integers(1, 30)))).isoformat()
    dirty.loc[idx, "Last_Sold_Date"] = future
    log["A4_future_date"] = {"rows": idx, "value": future, "cause": "POS terminal clock drift"}
    print(f"  💉 A4 Future Date        → {idx}  ({future})")

    # A5 — Stock outlier (ERP DB migration default)
    idx = rng.choice(n, size=k, replace=False).tolist()
    dirty.loc[idx, "Current_Stock"] = 99999
    log["A5_stock_outlier"] = {"rows": idx, "cause": "ERP defaulted to max int on migration"}
    print(f"  💉 A5 Stock Outlier      → {idx}")

    # A6 — Duplicate rows (ETL cron ran twice)
    idx = rng.choice(n, size=k, replace=False).tolist()
    dirty = pd.concat([dirty, dirty.iloc[idx].copy()], ignore_index=True)
    log["A6_duplicate_rows"] = {"source_rows": idx, "cause": "ETL cron overlap; double insert"}
    print(f"  💉 A6 Duplicates         → {idx}  (total now {len(dirty)})")

    # A7 — Blank product name (operator skipped required field)
    idx = rng.choice(len(dirty), size=k, replace=False).tolist()
    dirty.loc[idx, "Product_Name"] = ""
    log["A7_blank_name"] = {"rows": idx, "cause": "Operator pressed Enter, skipped name field"}
    print(f"  💉 A7 Blank Name         → {idx}")

    dirty.to_csv(CORRUPTED_PATH, index=False)
    print(f"\n  Corrupted file → {CORRUPTED_PATH}  ({len(dirty)} rows)")
    return dirty, log


# ═══════════════════════════════════════════════════════════════
# CLEAN
# ═══════════════════════════════════════════════════════════════

def clean(dirty: pd.DataFrame, original: pd.DataFrame):
    df     = dirty.copy()
    report = {}
    print("\n🧹  Running cleaning pipeline...")

    # C-01 Negative stock → 0
    m = df["Current_Stock"] < 0
    report["C01_negative_stock"] = int(m.sum())
    df.loc[m, "Current_Stock"] = 0
    print(f"  ✅ C-01 Negative stock clamped       : {m.sum()}")

    # C-02 Null price → category median
    m = df["Retail_Price"].isna()
    report["C02_null_price"] = int(m.sum())
    df["Retail_Price"] = df["Retail_Price"].fillna(
        df.groupby("Category")["Retail_Price"].transform("median"))
    print(f"  ✅ C-02 Null prices → category median : {m.sum()}")

    # C-03 Price inversion → cost × 1.5
    m = df["Retail_Price"] <= df["Cost_Price"]
    report["C03_price_inversion"] = int(m.sum())
    df.loc[m, "Retail_Price"] = (df.loc[m, "Cost_Price"] * 1.5).round(2)
    print(f"  ✅ C-03 Price inversions corrected   : {m.sum()}")

    # C-04 Future dates → cap at today
    df["Last_Sold_Date"] = pd.to_datetime(df["Last_Sold_Date"], errors="coerce")
    today_ts = pd.Timestamp(TODAY)
    m = df["Last_Sold_Date"] > today_ts
    report["C04_future_dates"] = int(m.sum())
    df.loc[m, "Last_Sold_Date"] = today_ts
    df["Last_Sold_Date"] = df["Last_Sold_Date"].dt.date.astype(str)
    print(f"  ✅ C-04 Future dates clamped         : {m.sum()}")

    # C-05 Stock outlier → cap at p99
    p99 = original["Current_Stock"].quantile(0.99)
    m = df["Current_Stock"] > p99 * 2
    report["C05_stock_outlier"] = int(m.sum())
    df.loc[m, "Current_Stock"] = int(p99)
    print(f"  ✅ C-05 Stock outliers capped at {int(p99)}  : {m.sum()}")

    # C-06 Duplicates → keep first
    before = len(df)
    df = df.drop_duplicates(subset=["Product_ID","SKU"], keep="first")
    report["C06_duplicates"] = before - len(df)
    print(f"  ✅ C-06 Duplicates removed           : {before - len(df)}")

    # C-07 Blank names → UNKNOWN_{ID}
    m = df["Product_Name"].isna() | (df["Product_Name"] == "")
    report["C07_blank_names"] = int(m.sum())
    df.loc[m, "Product_Name"] = "UNKNOWN_" + df.loc[m, "Product_ID"].astype(str)
    print(f"  ✅ C-07 Blank names filled           : {m.sum()}")

    # C-08 Recompute derived columns
    df["Margin_Pct"]     = ((df["Retail_Price"] - df["Cost_Price"]) / df["Retail_Price"] * 100).round(1)
    df["Low_Stock_Flag"] = (df["Current_Stock"] < 10).astype(int)
    df["Last_Sold_Date_dt"] = pd.to_datetime(df["Last_Sold_Date"], errors="coerce")
    df["Days_Since_Sale"]   = (pd.Timestamp(TODAY) - df["Last_Sold_Date_dt"]).dt.days.fillna(999).astype(int)
    df["Dead_Stock_Flag"]   = (df["Days_Since_Sale"] > 60).astype(int)
    df = df.drop(columns=["Last_Sold_Date_dt"])
    print(f"  ✅ C-08 Derived columns recomputed")

    df.to_csv(CLEAN_PATH, index=False)
    print(f"\n  Clean file → {CLEAN_PATH}  ({len(df)} rows)")
    return df, report


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n💀  Chaos Monkey — Week 4")
    print("=" * 60)

    if not os.path.exists(INVENTORY_PATH):
        print(f"  ⚠️  {INVENTORY_PATH} not found — run generate_mock_data.py first")
        exit(1)

    original  = pd.read_csv(INVENTORY_PATH)
    print(f"\n  Loaded {INVENTORY_PATH} : {len(original)} rows")

    corrupted, inj_log  = inject(original)
    clean_df,  cln_log  = clean(corrupted, original)

    result = {
        "run_timestamp":   datetime.now().isoformat(),
        "original_rows":   len(original),
        "corrupted_rows":  len(corrupted),
        "clean_rows":      len(clean_df),
        "pipeline_passed": len(clean_df) == len(original),
        "injection_log":   inj_log,
        "cleaning_report": cln_log,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n📄  Report → {REPORT_PATH}")
    print(f"\n  RESULT: {'✅ PASSED' if result['pipeline_passed'] else '❌ FAILED'}")
    print(f"  Original → Corrupted → Clean : {len(original)} → {len(corrupted)} → {len(clean_df)}\n")