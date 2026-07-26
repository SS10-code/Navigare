"""
dashboard.py — Navigare Retail Analytics  v5
Week 8 · Inventory Health Score + Caching Layer + Full Feature Suite

New this week:
  - @st.cache_data on ALL data loads (RAM architecture, disk I/O exactly once)
  - st.cache_data.clear() refresh button in sidebar
  - Inventory Health page rebuilt with H(x), wellness index μ, boolean mask M
  - Defensive guard walls (N=0 / N>0 branching) on every page
  - Priority alert dispatch panel
  - Full H(x) gauge chart per SKU

Run:  streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings, os, json, random, sys
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))
from seo_engine import analyse_text, score_density, normalize
from inventory_health import (run_inventory_health_pipeline,
                               aggregate_wellness_index,
                               boolean_mask_critical, H)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Navigare · Retail Analytics",
                   page_icon="🧭", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]  {background:#07101e;}
[data-testid="stSidebar"]           {background:#050c18;border-right:1px solid #0c1c35;}
.main .block-container              {padding:2rem 2.5rem 4rem;max-width:1300px;}

div[data-testid="stSidebar"] .stButton>button {
    width:100%;text-align:left;background:transparent;border:none;
    border-radius:8px;color:#405f8a;padding:9px 13px;
    font-size:13px;font-weight:500;transition:all .12s;margin-bottom:2px;
}
div[data-testid="stSidebar"] .stButton>button:hover{background:#0a1c35;color:#b8d0f0;}

.kpi-row{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;}
.kpi{flex:1;min-width:120px;background:linear-gradient(135deg,#090f1e,#0e1930);
    border:1px solid #0c2040;border-radius:11px;padding:14px 16px;}
.kpi-label{color:#2d4a70;font-size:10px;font-weight:700;text-transform:uppercase;
    letter-spacing:1px;margin-bottom:4px;}
.kpi-value{color:#ddeaff;font-size:22px;font-weight:800;line-height:1.1;}
.kpi-sub  {color:#1a3050;font-size:10.5px;margin-top:2px;}

.pg-title {font-size:20px;font-weight:800;color:#ddeaff;margin-bottom:3px;}
.pg-sub   {font-size:13px;color:#2d4a70;margin-bottom:20px;line-height:1.55;}

.explain  {background:#06101f;border-left:3px solid #1a45a8;border-radius:0 8px 8px 0;
    padding:12px 16px;margin:0 0 16px;color:#a0bce0;font-size:13px;line-height:1.7;}
.explain b{color:#5a9aff;}
.explain code{background:#0a1c3a;padding:1px 5px;border-radius:4px;
    font-size:11.5px;color:#7ee8a2;}
.warn     {background:#160b00;border-left:3px solid #c97a06;border-radius:0 8px 8px 0;
    padding:10px 14px;margin:0 0 14px;color:#f0b050;font-size:12.5px;}
.good     {background:#051408;border-left:3px solid #16a34a;border-radius:0 8px 8px 0;
    padding:10px 14px;margin:0 0 14px;color:#6ee7a0;font-size:12.5px;}
.crisis   {background:#1a0505;border-left:3px solid #ef4444;border-radius:0 8px 8px 0;
    padding:10px 14px;margin:0 0 14px;color:#fca5a5;font-size:12.5px;}
.formula  {background:#030c03;border:1px solid #183018;border-radius:8px;
    padding:12px 16px;font-family:monospace;font-size:12.5px;
    color:#6ee7b7;margin:10px 0;line-height:2;}
.sec      {font-size:10px;font-weight:700;color:#1a45a8;text-transform:uppercase;
    letter-spacing:1.2px;margin:24px 0 8px;}
.divider  {border:none;border-top:1px solid #0c1c35;margin:20px 0;}

/* Health status badges */
.badge{display:inline-block;padding:3px 10px;border-radius:20px;
    font-size:11px;font-weight:700;letter-spacing:.5px;}
.badge-crisis   {background:#3a0505;color:#ef4444;border:1px solid #ef4444;}
.badge-critical {background:#2a1200;color:#f97316;border:1px solid #f97316;}
.badge-low      {background:#1a1500;color:#eab308;border:1px solid #eab308;}
.badge-warning  {background:#101a00;color:#84cc16;border:1px solid #84cc16;}
.badge-healthy  {background:#051a05;color:#22c55e;border:1px solid #22c55e;}
.badge-optimal  {background:#001a1a;color:#06b6d4;border:1px solid #06b6d4;}
.badge-overstock{background:#150a1a;color:#a855f7;border:1px solid #a855f7;}

/* Alert cards */
.alert-card{border-radius:10px;padding:14px 18px;margin-bottom:10px;
    display:flex;align-items:center;gap:16px;}
.alert-crisis  {background:#1a0505;border:1px solid #ef4444;}
.alert-critical{background:#1a0a00;border:1px solid #f97316;}
.alert-low     {background:#1a1400;border:1px solid #eab308;}

/* Glossary */
.gcard{background:#06101f;border:1px solid #0c2040;border-radius:9px;
    padding:12px 16px;margin-bottom:10px;}
.gcard-term{font-size:13.5px;font-weight:700;color:#5a9aff;margin-bottom:5px;}
.gcard-plain{font-size:12.5px;color:#a0bce0;margin-bottom:7px;line-height:1.6;}
.gcard-formula{font-family:monospace;font-size:11.5px;color:#6ee7b7;
    background:#030c03;border-radius:4px;padding:5px 9px;display:inline-block;}
</style>
""", unsafe_allow_html=True)

BL="#3b6fd4";BY="#f59e0b";BG="#22c55e";BP="#a855f7";BR="#ef4444";BC="#06b6d4"
PLT=dict(template="plotly_dark",paper_bgcolor="#07101e",plot_bgcolor="#090f22")
SEV_COLOR={"none":BG,"low":"#86efac","medium":BY,"high":"#f97316","critical":BR}
STATUS_COLOR={"CRISIS":BR,"CRITICAL":"#f97316","LOW":BY,"WARNING":"#84cc16",
              "HEALTHY":BG,"OPTIMAL":BC,"OVERSTOCK":BP}


# ═════════════════════════════════════════════════════════════
# CACHING LAYER — Week 8 RAM Architecture
# Each function is decorated with @st.cache_data.
# Streamlit executes the disk read EXACTLY ONCE on startup,
# then serves subsequent calls directly from background RAM.
# The hash of the function arguments is used as the cache key —
# if args haven't changed, disk I/O is bypassed entirely.
# Latency: cache hit < 0.1s vs disk read ~250ms.
# ═════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_transactions() -> pd.DataFrame:
    """Ingests unified transaction ledger from disk. Cached in RAM after first load."""
    for path in ["data/clean/unified_transactions.csv","data/raw/transactions.csv"]:
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["Transaction_Date"])
            if "Store_Type" not in df.columns or df["Store_Type"].isna().all():
                df["Store_Type"] = df.get("Source_Currency", pd.Series()).map(
                    {"BRL":"E-Commerce","GBP":"Brick-and-Mortar"}).fillna("E-Commerce")
            if "Line_Total_USD" not in df.columns and "Line_Total" in df.columns:
                df["Line_Total_USD"] = df["Line_Total"]
            if "Line_Total" not in df.columns and "Line_Total_USD" in df.columns:
                df["Line_Total"] = df["Line_Total_USD"]
            return df
    # Fallback synthetic (no files found)
    rng = np.random.default_rng(42); random.seed(42)
    TODAY = datetime.today().date()
    cats=["Pastries","Breads","Cakes","Drinks","Savory"]
    types=["E-Commerce","Brick-and-Mortar"]
    base=datetime.combine(TODAY-timedelta(days=365),datetime.min.time())
    rows=[]
    for i in range(1200):
        st_=random.choice(types); ts=base+timedelta(days=int(rng.integers(0,364)),hours=int(rng.integers(8,20)),minutes=int(rng.integers(0,59)))
        p=round(float(rng.uniform(2.5,35)),2); q=int(rng.integers(1,6))
        rows.append({"Store_Type":st_,"Transaction_ID":f"TXN-{i:05d}","Customer_ID":f"C{rng.integers(1,61):04d}","Product_ID":int(rng.integers(1,26)),"Item_Price_USD":p,"Quantity":q,"Line_Total_USD":round(p*q,2),"Line_Total":round(p*q,2),"Transaction_Date":base.date()+timedelta(days=int(rng.integers(0,364))),"Category":random.choice(cats),"Source_Currency":"BRL" if st_=="E-Commerce" else "GBP"})
    df=pd.DataFrame(rows); df["Transaction_Date"]=pd.to_datetime(df["Transaction_Date"])
    return df

@st.cache_data(show_spinner=False)
def load_inventory() -> pd.DataFrame:
    """Loads inventory from disk once; serves from RAM on reruns."""
    for path in ["data/clean/inventory_clean.csv","data/raw/inventory.csv"]:
        if os.path.exists(path):
            return pd.read_csv(path)
    return None

@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    """Generic cached CSV loader — hits disk exactly once per unique path."""
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

@st.cache_data(show_spinner=False)
def load_csv_dates(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["Date"])
    return None

@st.cache_data(show_spinner=False)
def load_chaos() -> dict:
    path = "data/clean/chaos_report.json"
    if os.path.exists(path):
        with open(path) as f: return json.load(f)
    return None

@st.cache_data(show_spinner=False)
def load_daily(txn_df: pd.DataFrame) -> pd.DataFrame:
    """Computes daily revenue series once; cached keyed on the transaction DataFrame hash."""
    daily = (txn_df.groupby("Transaction_Date")["Line_Total_USD"]
             .sum().resample("D").sum().fillna(0).reset_index())
    daily.columns = ["Date","Revenue_USD"]
    return daily.sort_values("Date").reset_index(drop=True)

# Cached H(x) pipeline — expensive row-wise map runs once per inventory hash
@st.cache_data(show_spinner=False)
def load_health(inv_df: pd.DataFrame):
    if inv_df is None or len(inv_df) == 0:
        return None, {"wellness_score":0,"interpretation":"No data","N":0,"status_counts":{}}, pd.DataFrame()
    return run_inventory_health_pipeline(inv_df)

# ── Filter-aware derived metrics ──────────────────────────────
# These are cached but keyed on the FILTERED dataframe, so they
# automatically recompute when the store/date filter changes.
# Disk I/O already done — these are pure pandas operations on RAM data.

@st.cache_data(show_spinner=False)
def compute_filtered_product_metrics(txn: pd.DataFrame, inv_df: pd.DataFrame):
    """Product metrics computed from the current filter — responds to store/date selection."""
    if txn is None or len(txn) == 0 or inv_df is None: return None
    days = max(1, (txn["Transaction_Date"].max() - txn["Transaction_Date"].min()).days + 1)
    line_col = "Line_Total" if "Line_Total" in txn.columns else "Line_Total_USD"
    txn2 = txn.copy(); txn2["Product_ID"] = txn2["Product_ID"].astype(str)
    inv2 = inv_df.copy(); inv2["Product_ID"] = inv2["Product_ID"].astype(str)
    prod_txn = txn2.groupby("Product_ID").agg(
        Total_Units_Sold=("Quantity","sum"),
        Total_Revenue=(line_col,"sum"),
        Num_Transactions=("Transaction_ID","nunique"),
    ).reset_index()
    df = inv2.merge(prod_txn, on="Product_ID", how="left").fillna(0)
    df["Gross_Margin_Pct"] = ((df["Retail_Price"] - df["Cost_Price"]) / df["Retail_Price"].replace(0,1) * 100).round(1)
    df["Revenue_Per_Day"]  = (df["Total_Revenue"] / days).round(2)
    df["Units_Per_Day"]    = (df["Total_Units_Sold"] / days).round(2)
    df["Sell_Through_Pct"] = (df["Total_Units_Sold"] / (df["Total_Units_Sold"] + df["Current_Stock"]).replace(0,np.nan) * 100).round(1).fillna(0)
    keep = ["Product_ID","Product_Name","Category","Cost_Price","Retail_Price","Gross_Margin_Pct",
            "Current_Stock","Total_Units_Sold","Total_Revenue","Revenue_Per_Day","Sell_Through_Pct"]
    return df[[c for c in keep if c in df.columns]]

@st.cache_data(show_spinner=False)
def compute_filtered_rfm(txn: pd.DataFrame):
    """RFM scores computed from the current filter — responds to store/date selection."""
    if txn is None or len(txn) == 0: return None
    line_col = "Line_Total" if "Line_Total" in txn.columns else "Line_Total_USD"
    snapshot = txn["Transaction_Date"].max() + pd.Timedelta(days=1)
    rfm = txn.groupby("Customer_ID").agg(
        Last_Purchase=("Transaction_Date","max"),
        Frequency=("Transaction_ID","nunique"),
        Monetary=(line_col,"sum"),
    ).reset_index()
    rfm["Recency_Days"] = (snapshot - rfm["Last_Purchase"]).dt.days
    if len(rfm) < 3: return rfm  # not enough data for qcut
    try:
        rfm["R_Score"] = pd.qcut(rfm["Recency_Days"],  q=3, labels=[3,2,1]).astype(int)
        rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"),  q=3, labels=[1,2,3]).astype(int)
        rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"),   q=3, labels=[1,2,3]).astype(int)
    except Exception:
        rfm["R_Score"] = rfm["F_Score"] = rfm["M_Score"] = 2
    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]
    rfm["Segment"] = rfm["RFM_Score"].apply(lambda s: "Champion" if s>=8 else ("Loyal" if s>=6 else ("Potential" if s>=4 else "At Risk")))
    rfm["Last_Purchase"] = rfm["Last_Purchase"].dt.date
    rfm["Monetary"] = rfm["Monetary"].round(2)
    return rfm

@st.cache_data(show_spinner=False)
def compute_filtered_combo(txn: pd.DataFrame):
    """Market basket pairs computed from the current filter — responds to store/date selection."""
    from itertools import combinations as _comb
    if txn is None or len(txn) == 0: return None
    name_col = "Product_Name" if "Product_Name" in txn.columns else "Product_ID"
    orders = txn.groupby("Transaction_ID")["Product_ID"].apply(set).reset_index()
    orders.columns = ["Transaction_ID","Products"]
    total = len(orders)
    if total == 0: return None
    prod_sup = {}
    for prods in orders["Products"]:
        for p in prods: prod_sup[p] = prod_sup.get(p,0) + 1
    pair_counts = {}
    for prods in orders[orders["Products"].apply(len)>=2]["Products"]:
        for pair in _comb(sorted(prods),2):
            pair_counts[pair] = pair_counts.get(pair,0) + 1
    results = []
    for (pa,pb), count in pair_counts.items():
        sup = count/total
        if sup < 0.02: continue
        conf = count / prod_sup.get(pa,1)
        sup_b = prod_sup.get(pb,1)/total
        lift = conf/sup_b if sup_b>0 else 0
        results.append({"Product_A_ID":pa,"Product_B_ID":pb,"Co_Occurrences":count,
                        "Support":round(sup,4),"Confidence_AB":round(conf,4),"Lift":round(lift,3)})
    if not results: return None
    df = pd.DataFrame(results).sort_values("Lift",ascending=False).head(30)
    name_map = txn[["Product_ID",name_col]].drop_duplicates().set_index("Product_ID")[name_col]
    df["Product_A"] = df["Product_A_ID"].map(name_map)
    df["Product_B"] = df["Product_B_ID"].map(name_map)
    df["Pair_Label"] = df["Product_A"].astype(str) + "  +  " + df["Product_B"].astype(str)
    return df[["Pair_Label","Product_A","Product_B","Co_Occurrences","Support","Confidence_AB","Lift"]].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# LOAD ALL DATA
# ─────────────────────────────────────────────────────────────
with st.spinner("Booting Navigare — loading from disk…"):
    txn_df   = load_transactions()
    inv_raw  = load_inventory()
    daily_df = load_daily(txn_df)

    # Static reference data (not filter-sensitive — same regardless of store)
    inv_metrics  = load_csv("data/clean/inventory_metrics.csv")
    feat_df      = load_csv_dates("data/clean/features.csv")
    ema_df       = load_csv_dates("data/clean/ema_forecast.csv")
    adf_df       = load_csv("data/clean/adf_results.csv")
    vif_df       = load_csv("data/clean/vif_results.csv")
    chaos        = load_chaos()

    # H(x) pipeline — keyed on inventory (not filter-sensitive)
    health_df, wellness, critical_df = load_health(inv_raw)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style='padding:12px 0 16px'>
      <div style='font-size:19px;font-weight:800;color:#ddeaff;letter-spacing:-.3px'>🧭 Navigare</div>
      <div style='font-size:10px;color:#1a3050;margin-top:2px'>Retail Analytics · Phase 3</div>
    </div>""", unsafe_allow_html=True)

    PAGES = {
        "📊  Overview":            "overview",
        "📦  Inventory Health":    "inventory",
        "🛒  What Sells Together": "combo",
        "👥  Customer Segments":   "customers",
        "📈  Sales Forecast":      "forecast",
        "🔍  SEO Auditor":         "seo",
        "🔬  Under the Hood":      "features",
        "📖  Glossary":            "glossary",
    }
    if "page" not in st.session_state:
        st.session_state.page = "overview"
    for label, key in PAGES.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key; st.rerun()

    st.markdown("<hr style='border-color:#0c1c35;margin:14px 0'>", unsafe_allow_html=True)

    # Global filters
    st.markdown("<div style='font-size:10px;color:#1a3050;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px'>Filters</div>", unsafe_allow_html=True)
    store_opts = ["All Stores"] + sorted(txn_df["Store_Type"].dropna().unique().tolist())
    sel_store  = st.selectbox("Store", store_opts, label_visibility="collapsed")
    d_min = txn_df["Transaction_Date"].min().date()
    d_max = txn_df["Transaction_Date"].max().date()
    dr    = st.date_input("Dates", (d_min, d_max), min_value=d_min, max_value=d_max,
                          label_visibility="collapsed")

    st.markdown("<hr style='border-color:#0c1c35;margin:14px 0'>", unsafe_allow_html=True)

    # Store wellness badge in sidebar
    ws = wellness.get("wellness_score", 0)
    ws_color = wellness.get("color", BL)
    st.markdown(f"""
    <div style='margin-bottom:12px'>
      <div style='font-size:10px;color:#1a3050;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px'>Store Wellness</div>
      <div style='font-size:28px;font-weight:800;color:{ws_color};line-height:1'>{ws}/100</div>
      <div style='font-size:11px;color:{ws_color};margin-top:2px'>{wellness.get("interpretation","—")}</div>
    </div>""", unsafe_allow_html=True)

    # CRITICAL ALERTS COUNT
    n_crisis = len(critical_df) if critical_df is not None and len(critical_df) > 0 else 0
    if n_crisis > 0:
        st.markdown(f"""<div style='background:#1a0505;border:1px solid #ef4444;border-radius:8px;
            padding:10px 14px;margin-bottom:12px'>
          <div style='font-size:11px;font-weight:700;color:#ef4444'>🚨  {n_crisis} PRIORITY ALERTS</div>
          <div style='font-size:10px;color:#fca5a5;margin-top:2px'>SKUs needing immediate action</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:10px;color:#1a3050'>{d_min} → {d_max}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#0c1c35;margin:14px 0'>", unsafe_allow_html=True)

    # RAM FLUSH BUTTON — Week 8: cache invalidation
    # Placed AFTER filters so clearing cache doesn't wipe the filter state mid-render
    st.markdown("<div style='font-size:10px;color:#1a3050;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px'>Cache Control</div>", unsafe_allow_html=True)
    if st.button("↻  Refresh Data", use_container_width=True,
                 help="Clears RAM cache and re-reads all CSVs from disk. Use after updating data files."):
        st.cache_data.clear()
        st.rerun()
    st.caption("Cached in RAM for speed.\nRefresh after updating CSV files.")


# ─────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────
filt = txn_df.copy()
if sel_store != "All Stores":
    filt = filt[filt["Store_Type"] == sel_store]
if len(dr) == 2:
    filt = filt[(filt["Transaction_Date"].dt.date >= dr[0]) &
                (filt["Transaction_Date"].dt.date <= dr[1])]
ds = filt.groupby("Transaction_Date")["Line_Total_USD"].sum().resample("D").sum().fillna(0)

# ── Filter-aware derived metrics (recompute when store/date changes) ──
# Cached via @st.cache_data keyed on filt hash — no extra disk I/O
prod_df  = compute_filtered_product_metrics(filt, inv_raw)
rfm_df   = compute_filtered_rfm(filt)
combo_df = compute_filtered_combo(filt)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def kpis(metrics):
    html = '<div class="kpi-row">'
    for l, v, s in metrics:
        html += f'<div class="kpi"><div class="kpi-label">{l}</div><div class="kpi-value">{v}</div><div class="kpi-sub">{s}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def sec(t):   st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
def expl(t):  st.markdown(f'<div class="explain">{t}</div>', unsafe_allow_html=True)
def warn(t):  st.markdown(f'<div class="warn">{t}</div>', unsafe_allow_html=True)
def good(t):  st.markdown(f'<div class="good">{t}</div>', unsafe_allow_html=True)
def crisis(t):st.markdown(f'<div class="crisis">{t}</div>', unsafe_allow_html=True)
def fml(t):   st.markdown(f'<div class="formula">{t}</div>', unsafe_allow_html=True)

def status_badge(status):
    cls = f"badge-{status.lower()}"
    return f'<span class="badge {cls}">{status}</span>'

def guard_wall(df, name="data"):
    """Defensive guard wall — halt math if N=0, show safe UI."""
    if df is None or len(df) == 0:
        st.info(f"No {name} loaded. Run the pipeline scripts first, then click ↻ Refresh Data.")
        return False
    return True


# ═════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═════════════════════════════════════════════════════════════
if st.session_state.page == "overview":
    st.markdown('<div class="pg-title">📊 Store Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Everything at a glance. Filters in the sidebar apply to all charts.</div>', unsafe_allow_html=True)

    # Guard wall
    if not guard_wall(filt, "transaction data"): st.stop()

    rev    = filt["Line_Total_USD"].sum()
    orders = filt["Transaction_ID"].nunique()
    aov    = filt.groupby("Transaction_ID")["Line_Total_USD"].sum().mean() if orders > 0 else 0

    kpis([
        ("Revenue",         f"${rev:,.0f}",    sel_store),
        ("Orders",          f"{orders:,}",      "transactions"),
        ("Avg Order Value", f"${aov:,.2f}",     "per checkout"),
        ("Store Wellness",  f"{ws}/100",         wellness.get("interpretation","—")),
        ("Priority Alerts", f"{n_crisis}",      "SKUs need action"),
    ])

    c1, c2 = st.columns([3, 1])
    with c1:
        sec("Daily Revenue")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ds.index, y=ds.values, fill="tozeroy",
            fillcolor="rgba(59,111,212,0.08)", line=dict(color=BL, width=2), name="Daily"))
        roll = ds.rolling(7, min_periods=1).mean()
        fig.add_trace(go.Scatter(x=roll.index, y=roll.values,
            line=dict(color=BY, width=2, dash="dash"), name="7-day avg"))
        fig.update_layout(**PLT, height=300, hovermode="x unified",
            margin=dict(l=0,r=0,t=8,b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        if sel_store == "All Stores":
            sec("By Channel")
            rv = filt.groupby("Store_Type")["Line_Total_USD"].sum().reset_index()
            fig_pie = px.pie(rv, values="Line_Total_USD", names="Store_Type",
                color_discrete_sequence=[BL, BY], hole=0.55)
            fig_pie.update_layout(**PLT, height=250, margin=dict(l=0,r=0,t=0,b=0),
                showlegend=True, legend=dict(orientation="h", y=-0.15))
            fig_pie.update_traces(textinfo="percent+label", textfont_size=10)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            sec("By Category")
            rv = filt.groupby("Category")["Line_Total_USD"].sum().reset_index() if "Category" in filt.columns else pd.DataFrame()
            if len(rv) > 0:
                fig_pie = px.pie(rv, values="Line_Total_USD", names="Category",
                    color_discrete_sequence=px.colors.qualitative.Bold, hole=0.55)
                fig_pie.update_layout(**PLT, height=250, margin=dict(l=0,r=0,t=0,b=0),
                    showlegend=True, legend=dict(orientation="h", y=-0.15))
                fig_pie.update_traces(textinfo="percent+label", textfont_size=10)
                st.plotly_chart(fig_pie, use_container_width=True)

    if prod_df is not None and len(prod_df) > 0:
        sec("Top Products by Revenue")
        top = prod_df.nlargest(10, "Total_Revenue")
        fig_b = go.Figure(go.Bar(x=top["Total_Revenue"], y=top["Product_Name"],
            orientation="h", marker_color=BL,
            text=[f"${v:,.0f}" for v in top["Total_Revenue"]], textposition="outside"))
        fig_b.update_layout(**PLT, height=300, margin=dict(l=0,r=0,t=8,b=0))
        st.plotly_chart(fig_b, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# PAGE: INVENTORY HEALTH  ← Fully rebuilt with Week 8 math
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "inventory":
    st.markdown('<div class="pg-title">📦 Inventory Health</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Every SKU gets a health score from 0–100 via the H(x) function. The store wellness index μ is the arithmetic mean across all scores.</div>', unsafe_allow_html=True)

    # Guard wall: N=0
    if not guard_wall(inv_raw, "inventory"): st.stop()
    if not guard_wall(health_df, "health scores"): st.stop()

    # ── Wellness index KPI ────────────────────────────────────
    ws_color = wellness.get("color", BL)
    sc = wellness.get("status_counts", {})
    kpis([
        ("Store Wellness μ",  f"{ws}/100",              wellness.get("interpretation","—")),
        ("SKUs Tracked",      f"{wellness.get('N',0)}", "products"),
        ("🔴 CRISIS + CRITICAL", f"{sc.get('CRISIS',0) + sc.get('CRITICAL',0)}", "expedite now"),
        ("🟡 LOW",            f"{sc.get('LOW',0)}",     "order now"),
        ("🟢 HEALTHY + OPTIMAL",f"{sc.get('HEALTHY',0)+sc.get('OPTIMAL',0)}", "no action"),
    ])

    expl(f"""<b>H(x) — Asymmetric Inventory Health Function</b><br><br>
    Each SKU's current stock is fed into H(x), which returns a score 0–100.
    The function is <b>asymmetric</b> — running out of stock is far more damaging
    than having too much, so penalties below the reorder point are steep.<br><br>
    <b>Store Wellness Index</b> μ = (1/N) × Σ H(x_i) = <b>{ws}/100</b><br>
    This is the arithmetic mean of all health scores — the single number that
    summarises the entire store's stock position at a glance.""")

    # ── Wellness gauge ────────────────────────────────────────
    sec("Store Wellness Index  μ")
    g1, g2 = st.columns([1, 3])
    with g1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=ws,
            delta={"reference": 70, "valueformat": ".1f"},
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor="#1a3050"),
                bar=dict(color=ws_color),
                bgcolor="#07101e",
                steps=[
                    dict(range=[0,  20], color="#3a0505"),
                    dict(range=[20, 40], color="#2a1200"),
                    dict(range=[40, 60], color="#1a1400"),
                    dict(range=[60, 80], color="#101a00"),
                    dict(range=[80,100], color="#051a05"),
                ],
                threshold=dict(line=dict(color=BY, width=2), thickness=0.75, value=70)
            ),
            number=dict(suffix="/100", font=dict(color=ws_color, size=32)),
            title=dict(text=wellness.get("interpretation",""), font=dict(color=ws_color, size=13)),
        ))
        fig_gauge.update_layout(**PLT, height=280, margin=dict(l=20,r=20,t=20,b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with g2:
        # H(x) score per SKU bar chart
        hdf_sorted = health_df.sort_values("Health_Score")
        name_col   = "Product_Name" if "Product_Name" in hdf_sorted.columns else "Product_ID"
        fig_h = go.Figure(go.Bar(
            x=hdf_sorted["Health_Score"],
            y=hdf_sorted[name_col],
            orientation="h",
            marker_color=hdf_sorted["Health_Color"].tolist(),
            text=[f"{v}/100" for v in hdf_sorted["Health_Score"]],
            textposition="outside",
        ))
        fig_h.add_vline(x=70, line_color="#1a3050", line_dash="dash", line_width=1,
                        annotation_text="Healthy threshold", annotation_font_color="#405f8a",
                        annotation_font_size=10)
        fig_h.update_layout(**PLT, height=560, margin=dict(l=0,r=60,t=10,b=0),
            xaxis=dict(range=[0, 115], title="H(x) Health Score"),
            yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig_h, use_container_width=True)

    # ── Priority Alert Dispatch (Boolean Mask M=1) ───────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    sec("🚨 Priority Alert Dispatch  ·  Boolean Mask M = 1")
    expl("""<b>Boolean Masking Matrix:</b>  M_i = 1 if status is CRISIS, CRITICAL, or LOW  |  M_i = 0 otherwise<br>
    Only M=1 rows are surfaced here. The backend computes the mask; the UI renders the alerts.
    This is <b>Layout Presentation Separation</b> — math and display are decoupled.""")

    if critical_df is None or len(critical_df) == 0:
        good("✅  No priority alerts — all SKUs above LOW threshold.")
    else:
        # Group by status
        for status in ["CRISIS", "CRITICAL", "LOW"]:
            grp = critical_df[critical_df["Health_Status"] == status]
            if len(grp) == 0: continue
            cls_map = {"CRISIS":"crisis","CRITICAL":"warn","LOW":"warn"}
            badge_cls = {"CRISIS":"badge-crisis","CRITICAL":"badge-critical","LOW":"badge-low"}
            st.markdown(f'<div class="sec">{status} — {len(grp)} SKU{"s" if len(grp)>1 else ""}</div>', unsafe_allow_html=True)
            name_col = "Product_Name" if "Product_Name" in grp.columns else "Product_ID"
            for _, row in grp.iterrows():
                explanation = row.get("Health_Explanation", "")
                score = row.get("Health_Score", 0)
                stock = row.get("Current_Stock", "?")
                st.markdown(f"""
                <div class="alert-card alert-{status.lower()}">
                  <div style="font-size:28px;font-weight:800;color:{STATUS_COLOR.get(status,BL)}">{score}</div>
                  <div style="flex:1">
                    <div style="font-weight:700;color:#ddeaff;font-size:14px">{row.get(name_col,'—')}</div>
                    <div style="font-size:12px;color:#a0bce0;margin-top:2px">{explanation}</div>
                  </div>
                  <div style="text-align:right">
                    <div style="font-size:22px;font-weight:800;color:#ddeaff">{int(stock)}</div>
                    <div style="font-size:10px;color:#405f8a">units</div>
                  </div>
                </div>""", unsafe_allow_html=True)

    # ── ROP Chart ────────────────────────────────────────────
    if inv_metrics is not None and len(inv_metrics) > 0:
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        sec("Current Stock vs Reorder Point")
        fig_rop = go.Figure()
        fig_rop.add_trace(go.Bar(name="Current Stock",
            x=inv_metrics["Product_Name"], y=inv_metrics["Current_Stock"],
            marker_color=[STATUS_COLOR.get(s, BL) for s in (health_df["Health_Status"].tolist() if health_df is not None and "Health_Status" in health_df.columns else [BL]*len(inv_metrics))]))
        fig_rop.add_trace(go.Scatter(name="Reorder Point (ROP)",
            x=inv_metrics["Product_Name"], y=inv_metrics["ROP"],
            mode="markers", marker=dict(symbol="line-ew", size=14, color=BR,
                                        line=dict(width=2, color=BR))))
        fig_rop.add_trace(go.Scatter(name="Safety Stock",
            x=inv_metrics["Product_Name"], y=inv_metrics["Safety_Stock"],
            mode="lines", line=dict(color=BY, width=1.5, dash="dot")))
        fig_rop.update_layout(**PLT, height=360, hovermode="x", barmode="overlay",
            margin=dict(l=0,r=0,t=8,b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_rop.update_xaxes(tickangle=-40, tickfont=dict(size=9))
        st.plotly_chart(fig_rop, use_container_width=True)
        warn("Any product where the bar (current stock) is below the red dash (ROP) needs ordering today.")

    # ── Full health table ─────────────────────────────────────
    sec("Full Health Table")
    fml("x = [stock_1, stock_2, ..., stock_n]  →  h = [H(x_1), H(x_2), ..., H(x_n)]  →  μ = (1/N)Σh_i")
    disp_cols = ["Product_Name","Category","Current_Stock","Health_Score","Health_Status","Health_Explanation"]
    if health_df is not None:
        disp = health_df[[c for c in disp_cols if c in health_df.columns]].copy()
        disp = disp.sort_values("Health_Score")
        st.dataframe(disp, use_container_width=True, height=360)

    # ── H(x) curve ───────────────────────────────────────────
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    sec("H(x) Scoring Curve — Why It's Asymmetric")
    expl("""The steepest drop is on the left side (near zero). Running out costs more than overstocking —
    immediate sale loss plus long-term customer retention decay. The right side has a gentle dip
    for overstock to represent holding costs and capital lock-up, but never drops to zero.""")
    x_range = np.arange(0, 151, 1)
    y_scores = [H(float(x))["score"] for x in x_range]
    y_status = [H(float(x))["status"] for x in x_range]
    zone_colors = [STATUS_COLOR.get(s, BL) for s in y_status]
    fig_hx = go.Figure()
    fig_hx.add_trace(go.Scatter(x=x_range, y=y_scores,
        mode="lines", line=dict(color=BL, width=3), name="H(x)"))
    fig_hx.add_scatter(x=x_range, y=y_scores,
        mode="markers", marker=dict(color=zone_colors, size=4), showlegend=False)
    fig_hx.add_vline(x=10,  line_color="#1a3050", line_dash="dash", line_width=1,
                     annotation_text="ROP=10", annotation_font_color="#405f8a", annotation_font_size=10)
    fig_hx.add_vline(x=100, line_color="#150a1a", line_dash="dash", line_width=1,
                     annotation_text="Overstock=100", annotation_font_color="#a855f7", annotation_font_size=10)
    fig_hx.update_layout(**PLT, height=280, xaxis_title="Current Stock Units",
        yaxis_title="H(x) Health Score", margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig_hx, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# PAGE: WHAT SELLS TOGETHER
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "combo":
    st.markdown('<div class="pg-title">🛒 What Sells Together</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Products that customers frequently buy in the same order. Use this for bundles, promotions, and shelf placement.</div>', unsafe_allow_html=True)
    if not guard_wall(combo_df, "combo pairs"): st.stop()
    expl("""<b>Support</b> — % of orders with this pair.<br>
    <b>Confidence</b> — if A is in the cart, probability B is too.<br>
    <b>Lift > 1</b> — pair sells together more than random chance. Lift=2.5 means 2.5× more likely.<br>
    <b>Scalability:</b> 25 SKUs → 300 pairs checked directly. At 500+ SKUs, use FP-Growth algorithm.""")
    kpis([("Pairs Found",f"{len(combo_df)}","above threshold"),("Top Lift",f"{combo_df['Lift'].max():.2f}×","strongest link"),
          ("Avg Confidence",f"{combo_df['Confidence_AB'].mean():.1%}","A → buy B"),("Orders Scanned",f"{filt['Transaction_ID'].nunique():,}","basket patterns")])
    sec("Strongest Pairs (by Lift)")
    top = combo_df.head(15)
    fig_c = go.Figure(go.Bar(x=top["Lift"], y=top["Pair_Label"], orientation="h",
        marker_color=[BG if v>=2 else (BC if v>=1.5 else BL) for v in top["Lift"]],
        text=[f"{v:.2f}×" for v in top["Lift"]], textposition="outside"))
    fig_c.add_vline(x=1, line_color="#1a3050", line_dash="dash", line_width=1)
    fig_c.update_layout(**PLT, height=440, margin=dict(l=0,r=0,t=8,b=0), xaxis_title="Lift")
    st.plotly_chart(fig_c, use_container_width=True)
    sec("Full Pair Table")
    disp = combo_df.copy()
    disp["Support"] = disp["Support"].apply(lambda x: f"{x:.1%}")
    disp["Confidence_AB"] = disp["Confidence_AB"].apply(lambda x: f"{x:.1%}")
    disp["Lift"] = disp["Lift"].apply(lambda x: f"{x:.2f}×")
    disp.columns = ["Pair","Product A","Product B","Orders Together","Support","Confidence (A→B)","Lift"]
    st.dataframe(disp[["Pair","Orders Together","Support","Confidence (A→B)","Lift"]], use_container_width=True, height=300)


# ═════════════════════════════════════════════════════════════
# PAGE: CUSTOMERS
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "customers":
    st.markdown('<div class="pg-title">👥 Customer Segments</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">RFM scoring groups customers by how recently, how often, and how much they spend.</div>', unsafe_allow_html=True)
    if not guard_wall(rfm_df, "customer RFM data"): st.stop()
    expl("""<b>Recency (R)</b> — bought recently? 3=yes, 1=a while ago.<br>
    <b>Frequency (F)</b> — how often? 3=frequent, 1=one-time.<br>
    <b>Monetary (M)</b> — how much? 3=high spender, 1=low.<br>
    Score 3–9 → <b>Champion</b> (8–9) · <b>Loyal</b> (6–7) · <b>Potential</b> (4–5) · <b>At Risk</b> (3)""")
    seg_counts = rfm_df["Segment"].value_counts() if "Segment" in rfm_df.columns else pd.Series()
    seg_rev    = rfm_df.groupby("Segment")["Monetary"].sum() if "Segment" in rfm_df.columns else pd.Series()
    kpis([("Customers",f"{rfm_df['Customer_ID'].nunique()}",f"{sel_store}"),
          ("Champions",f"{seg_counts.get('Champion',0)}","top buyers"),
          ("Loyal",f"{seg_counts.get('Loyal',0)}","consistent"),
          ("At Risk",f"{seg_counts.get('At Risk',0)}","need attention"),
          ("Avg Spend",f"${rfm_df['Monetary'].mean():,.2f}","per customer")])
    SCOLS = {"Champion":BG,"Loyal":BL,"Potential":BC,"At Risk":BR}
    c1, c2 = st.columns(2)
    with c1:
        sec("Customers by Segment")
        fig_s = go.Figure(go.Bar(x=seg_counts.index, y=seg_counts.values,
            marker_color=[SCOLS.get(s,BL) for s in seg_counts.index],
            text=seg_counts.values, textposition="outside"))
        fig_s.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=8,b=0))
        st.plotly_chart(fig_s, use_container_width=True)
    with c2:
        sec("Revenue by Segment")
        fig_r = go.Figure(go.Bar(x=seg_rev.index, y=seg_rev.values,
            marker_color=[SCOLS.get(s,BL) for s in seg_rev.index],
            text=[f"${v:,.0f}" for v in seg_rev.values], textposition="outside"))
        fig_r.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=8,b=0), yaxis_title="Total Revenue ($)")
        st.plotly_chart(fig_r, use_container_width=True)
    sec("Recency vs Spend")
    fig_sc = px.scatter(rfm_df, x="Recency_Days", y="Monetary", color="Segment",
        size="Frequency", hover_data=["Customer_ID","Frequency"],
        color_discrete_map=SCOLS,
        labels={"Recency_Days":"Days Since Last Purchase","Monetary":"Total Spend ($)"})
    fig_sc.update_layout(**PLT, height=360, margin=dict(l=0,r=0,t=8,b=0))
    st.plotly_chart(fig_sc, use_container_width=True)
    sec("Customer Table")
    disp = rfm_df[["Customer_ID","Last_Purchase","Recency_Days","Frequency","Monetary",
                   "R_Score","F_Score","M_Score","RFM_Score","Segment"]].copy()
    disp["Monetary"] = disp["Monetary"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(disp, use_container_width=True, height=320)


# ═════════════════════════════════════════════════════════════
# PAGE: FORECAST
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "forecast":
    st.markdown('<div class="pg-title">📈 Sales Forecast</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Three forecasting models running side by side. Adjust the controls to see how each handles your data.</div>', unsafe_allow_html=True)
    if not guard_wall(filt, "transaction data"): st.stop()
    c1,c2,c3,c4 = st.columns(4)
    sma_w = c1.slider("Smoothing window", 3, 30, 7, help="Days averaged for SMA")
    ema_w = c2.slider("EMA window",       3, 30, 7, help="Larger = smoother, slower to react")
    sp    = c3.number_input("Seasonal period", 2, 30, 7, help="7 = weekly seasonality")
    fcd   = c4.slider("Forecast days",    7, 60, 14)
    alpha = 2/(ema_w+1)
    e1,e2,e3 = st.columns(3)
    with e1: expl(f"<b>Simple Moving Average</b><br>Averages last {sma_w} days equally. Smooth but lags behind changes.")
    with e2: expl(f"<b>Weighted Avg (EMA)</b><br>Recent days count more. α={alpha:.3f} — weight on most recent day.")
    with e3: expl(f"<b>Holt-Winters</b><br>Tracks trend + seasonality. Best when weekends differ from weekdays.")
    sma_s = ds.rolling(sma_w, min_periods=1).mean()
    ema_s = ds.ewm(span=ema_w, adjust=False).mean()
    hw_ok = False
    try:
        hw      = ExponentialSmoothing(ds, trend="add", seasonal="add",
                    seasonal_periods=int(sp), initialization_method="estimated").fit(optimized=True)
        hw_fit  = hw.fittedvalues
        fc_idx  = pd.date_range(ds.index[-1]+pd.Timedelta(days=1), periods=fcd, freq="D")
        hw_fc   = pd.Series(hw.forecast(fcd).values, index=fc_idx)
        hw_ok   = True
    except Exception as e:
        warn(f"Holt-Winters couldn't fit with these settings: {str(e)[:120]}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ds.index, y=ds.values, name="Actual",
        line=dict(color="#1e3a5a", width=1), opacity=0.8))
    fig.add_trace(go.Scatter(x=sma_s.index, y=sma_s.values,
        name=f"Simple avg ({sma_w}d)", line=dict(color=BY, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=ema_s.index, y=ema_s.values,
        name=f"Weighted avg ({ema_w}d)", line=dict(color=BC, width=2.5)))
    if hw_ok:
        fig.add_trace(go.Scatter(x=hw_fit.index, y=hw_fit.values,
            name="Holt-Winters fitted", line=dict(color=BG, width=2), opacity=0.85))
        fig.add_trace(go.Scatter(x=hw_fc.index, y=hw_fc.values,
            name=f"Forecast +{fcd}d", line=dict(color=BP, width=2.5, dash="dot"),
            fill="tozeroy", fillcolor="rgba(168,85,247,0.05)"))
        fig.add_vline(x=str(ds.index[-1]), line_color=BY, line_dash="dash", line_width=1,
                      annotation_text="  Today", annotation_font_color=BY, annotation_font_size=10)
    fig.update_layout(**PLT, height=400, hovermode="x unified", margin=dict(l=0,r=0,t=10,b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    if ema_df is not None:
        sec("14-Day Weighted Average Forecast")
        tc1, tc2 = st.columns([2, 1])
        with tc1:
            fig_e = go.Figure()
            fig_e.add_trace(go.Scatter(x=ds.index[-30:], y=ds.values[-30:],
                name="Last 30 days", line=dict(color=BL, width=2)))
            fig_e.add_trace(go.Scatter(x=ema_df["Date"], y=ema_df["EMA_Forecast"],
                name="Forecast", line=dict(color=BC, width=2.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(6,182,212,0.06)"))
            fig_e.update_layout(**PLT, height=240, hovermode="x unified", margin=dict(l=0,r=0,t=8,b=0))
            st.plotly_chart(fig_e, use_container_width=True)
        with tc2:
            d = ema_df[["Date","Day_Ahead","EMA_Forecast"]].copy()
            d["Date"] = pd.to_datetime(d["Date"]).dt.strftime("%b %d")
            d["EMA_Forecast"] = d["EMA_Forecast"].apply(lambda x: f"${x:,.2f}")
            d.columns = ["Date","Day","Forecast"]
            st.dataframe(d, use_container_width=True, height=240)
    if hw_ok:
        sec("Accuracy (average daily error)")
        act     = ds.reindex(hw_fit.index).fillna(0)
        hw_mae  = (act-hw_fit).abs().mean()
        sma_al  = sma_s.reindex(ds.index).ffill()
        sma_mae = (ds-sma_al).abs().mean()
        ema_al  = ema_s.reindex(ds.index)
        ema_mae = (ds-ema_al).abs().mean()
        ac1,ac2,ac3 = st.columns(3)
        winner  = min([("Simple avg",sma_mae),("Weighted avg",ema_mae),("Holt-Winters",hw_mae)], key=lambda x:x[1])
        for col,name,mae in [(ac1,"Simple avg",sma_mae),(ac2,"Weighted avg",ema_mae),(ac3,"Holt-Winters",hw_mae)]:
            badge = " 🏆" if name==winner[0] else ""
            col.metric(f"{name}{badge}", f"${mae:.2f}/day",
                       delta="most accurate" if name==winner[0] else None,
                       delta_color="normal" if name==winner[0] else "off")


# ═════════════════════════════════════════════════════════════
# PAGE: SEO AUDITOR
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "seo":
    st.markdown('<div class="pg-title">🔍 SEO Auditor</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Paste any web copy and check how well it\'s optimised for your target keywords. No live scraping, no API keys.</div>', unsafe_allow_html=True)
    expl("""<b>How it works:</b><br>
    1. Text is cleaned — lowercase, punctuation stripped, tokenised on whitespace<br>
    2. A sliding window scans for every keyword phrase (even multi-word ones like "fresh sourdough bread")<br>
    3. Density = matches ÷ total words × 100<br>
    4. Piecewise scoring: &lt;1% → 50, 1–3.5% → 100, &gt;3.5% → max(0, 100 − (excess × 15))""")
    col_text, col_kw = st.columns([2,1])
    with col_text:
        sec("Your Web Copy")
        body_text = st.text_area("Paste web copy", height=260,
            placeholder="Paste your homepage, product description, or Google Business listing here…",
            label_visibility="collapsed")
        if body_text.strip():
            wc = len(normalize(body_text))
            st.caption(f"Token count after normalisation: {wc}")
    with col_kw:
        sec("Target Keywords  (one per line)")
        default_kws = "bakery near me\nfresh bread\ncustom birthday cake\nartisan bakery\nsourdough loaf\nbest bakery\ncoffee and pastries"
        kw_text     = st.text_area("Keywords", value=default_kws, height=200, label_visibility="collapsed")
        remove_sw   = st.checkbox("Remove stop-words from token count", value=False)

    run_audit = st.button("▶  Run SEO Audit", type="primary")
    if run_audit:
        if not body_text.strip():
            st.error("Paste some web copy first.")
        else:
            keywords = [k.strip() for k in kw_text.strip().splitlines() if k.strip()]
            if not keywords:
                st.error("Add at least one keyword.")
            else:
                with st.spinner("Analysing…"):
                    report = analyse_text(body_text, keywords, remove_stopwords=remove_sw)
                if "error" in report:
                    st.error(report["error"])
                else:
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                    health   = report["page_health_score"]
                    hcol     = BG if health>=90 else (BC if health>=70 else (BY if health>=50 else BR))
                    hlabel   = "Excellent" if health>=90 else ("Good" if health>=70 else ("Needs Work" if health>=50 else "Poor"))
                    h1,h2,h3 = st.columns(3)
                    h1.markdown(f'<div class="kpi"><div class="kpi-label">Page Health Score</div><div class="kpi-value" style="color:{hcol};font-size:36px">{health}/100</div><div class="kpi-sub">{hlabel}</div></div>', unsafe_allow_html=True)
                    h2.markdown(f'<div class="kpi"><div class="kpi-label">Word Count</div><div class="kpi-value">{report["token_count"]}</div><div class="kpi-sub">tokens after normalisation</div></div>', unsafe_allow_html=True)
                    h3.markdown(f'<div class="kpi"><div class="kpi-label">Keywords Checked</div><div class="kpi-value">{report["keyword_count"]}</div><div class="kpi-sub">phrases analysed</div></div>', unsafe_allow_html=True)
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                    sec("Results per Keyword")
                    results   = report["results"]
                    kw_names  = [r["keyword"] for r in results if "score" in r]
                    kw_scores = [r["score"]   for r in results if "score" in r]
                    kw_dens   = [r["density_pct"] for r in results if "score" in r]
                    kw_sevs   = [r["severity"]    for r in results if "score" in r]
                    if kw_names:
                        fig_kw = go.Figure()
                        fig_kw.add_trace(go.Bar(name="Score", x=kw_names, y=kw_scores,
                            marker_color=[SEV_COLOR.get(s,BL) for s in kw_sevs],
                            text=[f"{v}/100" for v in kw_scores], textposition="outside", yaxis="y1"))
                        fig_kw.add_trace(go.Scatter(name="Density %", x=kw_names, y=kw_dens,
                            mode="lines+markers", line=dict(color=BY,width=2), marker=dict(size=8), yaxis="y2"))
                        fig_kw.add_hrect(y0=1.0, y1=3.5, fillcolor="rgba(34,197,94,0.05)",
                            line_width=0, yref="y2", annotation_text="Sweet spot",
                            annotation_font_color=BG, annotation_font_size=10)
                        fig_kw.update_layout(**PLT, height=340, hovermode="x unified", margin=dict(l=0,r=0,t=10,b=0),
                            yaxis=dict(title="SEO Score",range=[0,115]),
                            yaxis2=dict(title="Density %",overlaying="y",side="right",
                                        range=[0,max(kw_dens)*2+1] if kw_dens else [0,10]),
                            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                        st.plotly_chart(fig_kw, use_container_width=True)
                    for r in results:
                        if "error" in r: warn(f"'{r['keyword']}' — {r['error']}"); continue
                        sev = r["severity"]
                        icon = "✅" if sev=="none" else ("⚠️" if sev in ["medium","low"] else "🔴")
                        with st.expander(f"{icon}  \"{r['keyword']}\"  —  {r['score']}/100  ·  {r['zone']}"):
                            mc1,mc2,mc3,mc4 = st.columns(4)
                            mc1.metric("Score",f"{r['score']}/100")
                            mc2.metric("Matches",r["match_count"])
                            mc3.metric("Density",f"{r['density_pct']:.2f}%")
                            mc4.metric("N-Gram",f"{r['n_gram_size']} word{'s' if r['n_gram_size']>1 else ''}")
                            box = "good" if sev=="none" else ("crisis" if sev in ["critical","high"] else "warn")
                            st.markdown(f'<div class="{box}">{r["explanation"]}</div>', unsafe_allow_html=True)
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                    sec("Scoring Zone Curve")
                    x_rng = np.linspace(0,12,300)
                    y_sc  = [score_density(float(x))["score"] for x in x_rng]
                    fig_zone = go.Figure()
                    fig_zone.add_trace(go.Scatter(x=x_rng,y=y_sc,line=dict(color=BL,width=3),name="SEO Score"))
                    fig_zone.add_vrect(x0=0,x1=1.0,fillcolor="rgba(239,68,68,0.07)",line_width=0,annotation_text="Under-optimized",annotation_font_color=BR,annotation_font_size=10)
                    fig_zone.add_vrect(x0=1.0,x1=3.5,fillcolor="rgba(34,197,94,0.07)",line_width=0,annotation_text="Sweet Spot",annotation_font_color=BG,annotation_font_size=10)
                    fig_zone.add_vrect(x0=3.5,x1=12,fillcolor="rgba(245,158,11,0.05)",line_width=0,annotation_text="Penalty Zone",annotation_font_color=BY,annotation_font_size=10)
                    fig_zone.update_layout(**PLT,height=260,xaxis_title="Density (%)",yaxis_title="Score",margin=dict(l=0,r=0,t=30,b=0))
                    st.plotly_chart(fig_zone, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# PAGE: UNDER THE HOOD
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "features":
    st.markdown('<div class="pg-title">🔬 Under the Hood</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">The math behind the forecasting features. See the Glossary for plain-English definitions.</div>', unsafe_allow_html=True)
    if not guard_wall(feat_df, "feature data"): st.stop()
    sel = st.selectbox("Jump to",["Normalisation (Z-Score & Min-Max)","Time Encoding (Cyclic)","Memory Features (Lags)","Stationarity & Differencing","Feature Redundancy (VIF)"])
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    if "Normalisation" in sel:
        expl("Normalisation puts numbers on the same scale so models don't treat big dollar values as more important.")
        fml("Z = (x − μ) / σ              ← Z-Score\nX' = (x − min) / (max − min)  ← Min-Max")
        mu=feat_df["Revenue_USD"].mean();sigma=feat_df["Revenue_USD"].std();outs=(feat_df["Revenue_ZScore"].abs()>2).sum()
        m1,m2,m3=st.columns(3);m1.metric("Mean",f"${mu:,.2f}");m2.metric("Std Dev",f"${sigma:,.2f}");m3.metric("Outlier days",str(outs))
        fig_n=make_subplots(rows=2,cols=1,subplot_titles=("Z-Score","Min-Max"),vertical_spacing=0.14)
        fig_n.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_ZScore"],line=dict(color=BL,width=1.5),fill="tozeroy",fillcolor="rgba(59,111,212,0.07)"),row=1,col=1)
        for lvl,c in [(2,BR),(-2,BR),(0,"#0c1c35")]: fig_n.add_hline(y=lvl,line_color=c,line_dash="dot" if abs(lvl)==2 else "dash",line_width=1,row=1,col=1)
        fig_n.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_MinMax"],line=dict(color=BC,width=1.5),fill="tozeroy",fillcolor="rgba(6,182,212,0.07)"),row=2,col=1)
        fig_n.update_layout(**PLT,height=380,showlegend=False,margin=dict(l=0,r=0,t=28,b=0))
        st.plotly_chart(fig_n,use_container_width=True)
    elif "Cyclic" in sel:
        expl("Mon=1, Sun=7 tells a model they're far apart. They're adjacent. We place days on a circle so every day is equidistant from its neighbours.")
        fml("sin_dow = sin(2π × day / 7)\ncos_dow = cos(2π × day / 7)")
        dow_c=feat_df.groupby("day_of_week")[["sin_dow","cos_dow"]].first()
        dlbls=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];dcols=[BL,"#60a5fa","#93c5fd",BY,"#fcd34d","#f97316",BR]
        theta=np.linspace(0,2*np.pi,200);fig_circ=go.Figure()
        fig_circ.add_trace(go.Scatter(x=np.sin(theta),y=np.cos(theta),mode="lines",line=dict(color="#0c1c35",width=1.5),showlegend=False))
        dow_rev=feat_df.groupby("day_of_week")["Revenue_USD"].mean()
        for i,(dow,row) in enumerate(dow_c.iterrows()):
            fig_circ.add_trace(go.Scatter(x=[row["sin_dow"]],y=[row["cos_dow"]],mode="markers+text",marker=dict(size=20,color=dcols[i],line=dict(color="#07101e",width=2)),text=[f"<b>{dlbls[dow]}</b>"],textposition="top center",textfont=dict(color=dcols[i],size=11),name=f"{dlbls[dow]} (${dow_rev.get(dow,0):.0f}/day)"))
        fig_circ.update_layout(**PLT,height=400,xaxis=dict(range=[-1.6,1.6]),yaxis=dict(range=[-1.6,1.6]),margin=dict(l=0,r=0,t=40,b=0),legend=dict(font=dict(size=10),x=1.02,y=1))
        st.plotly_chart(fig_circ,use_container_width=True)
    elif "Memory" in sel:
        expl("A model sees one row at a time with no memory. Lag features copy past revenue into the current row so the model can look back.")
        warn("⚠️  Deployment leakage: forecasting 7 days ahead means Lag 1–6 don't exist at inference time. Minimum safe lag = 7.")
        fml("Y_t = f(Y_{t-1}, Y_{t-7}, ...) + ε")
        lag_max=st.slider("Lags to display",3,14,14)
        lag_cols=[f"lag_{i}" for i in range(1,lag_max+1)]
        corr_vals=[feat_df["Revenue_USD"].corr(feat_df[c]) for c in lag_cols]
        best=max(range(len(corr_vals)),key=lambda i:abs(corr_vals[i]))
        fig_lag=go.Figure(go.Bar(x=[f"Lag {i}" for i in range(1,lag_max+1)],y=corr_vals,marker_color=[BG if i==best else (BL if v>=0 else BR) for i,v in enumerate(corr_vals)],text=[f"{v:.3f}" for v in corr_vals],textposition="outside"))
        fig_lag.add_hline(y=0,line_color="#0c1c35",line_width=1)
        fig_lag.update_layout(**PLT,height=300,title=f"Lag {best+1} is the strongest predictor",yaxis_title="Pearson r",margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_lag,use_container_width=True)
    elif "Stationarity" in sel:
        expl("ARIMA needs a constant average over time. If revenue is trending up, we difference it: predict the daily change instead of the level.")
        fml("ΔY_t = Y_t − Y_{t-1}    ← predict change, not level")
        if adf_df is not None:
            for _,row in adf_df.iterrows():
                ok="YES" in str(row.get("Stationary",""))
                st.metric(row["Series"],f"p = {row['p_value']:.4f}",delta="✅ Stationary" if ok else "⚠️ Not stationary",delta_color="normal" if ok else "inverse")
        fig_d=make_subplots(rows=2,cols=1,subplot_titles=("Raw revenue","After differencing — bounces around 0"),vertical_spacing=0.14)
        fig_d.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_USD"],line=dict(color=BL,width=1.5),fill="tozeroy",fillcolor="rgba(59,111,212,0.07)"),row=1,col=1)
        fig_d.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["revenue_diff1"],line=dict(color=BY,width=1.5),fill="tozeroy",fillcolor="rgba(245,158,11,0.07)"),row=2,col=1)
        fig_d.add_hline(y=0,line_color="#0c1c35",line_dash="dash",row=2,col=1)
        fig_d.update_layout(**PLT,height=380,showlegend=False,margin=dict(l=0,r=0,t=28,b=0))
        st.plotly_chart(fig_d,use_container_width=True)
    elif "VIF" in sel:
        expl("VIF detects when two features say the same thing. High VIF → drop or combine with PCA before building XGBoost.")
        fml("VIF = 1/(1−R²)  ·  >10 = drop feature")
        if vif_df is not None:
            fig_vif=go.Figure(go.Bar(x=vif_df["VIF"],y=vif_df["Feature"],orientation="h",marker_color=["#ef4444" if v>10 else ("#f59e0b" if v>5 else "#22c55e") for v in vif_df["VIF"]],text=[f"{v:.1f}" for v in vif_df["VIF"]],textposition="outside"))
            fig_vif.add_vline(x=5,line_color=BY,line_dash="dot",line_width=1)
            fig_vif.add_vline(x=10,line_color=BR,line_dash="dot",line_width=1)
            fig_vif.update_layout(**PLT,height=360,title="green=keep · yellow=watch · red=drop",margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_vif,use_container_width=True)


# ═════════════════════════════════════════════════════════════
# PAGE: GLOSSARY
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "glossary":
    st.markdown('<div class="pg-title">📖 Glossary</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Plain-English definitions for every metric and concept. No prior knowledge required.</div>', unsafe_allow_html=True)
    G = [
        ("H(x) — Inventory Health Function","Asymmetric function applied row-wise to each SKU's stock count. Returns a score 0–100. Steep penalty near zero (sale loss + customer decay) vs gentle penalty for overstock (holding cost).","H(x): 0→CRISIS(0) · 1-5→CRITICAL(4-20) · 6-10→LOW(25-45)\n11-20→WARNING(52-70) · 21-50→HEALTHY(70-88) · 51-100→OPTIMAL(100) · >100→OVERSTOCK"),
        ("μ — Store Wellness Index","Arithmetic mean of all SKU health scores. The single number that summarises the entire store's stock position. μ = (1/N) × Σ H(x_i)","μ = (1/N) × Σ h_i  where h_i = H(stock_i)"),
        ("M — Boolean Masking Matrix","Binary flag per SKU. M=1 if status is CRISIS, CRITICAL, or LOW. The backend computes M; the UI only renders M=1 rows. This is Layout Presentation Separation.","M_i = 1 if status ∈ {CRISIS, CRITICAL, LOW}, else 0"),
        ("Understock Cost","The true cost of running out of stock: immediate sale loss PLUS long-term customer retention decay. Customers who can't find what they need don't always come back.","Cost(understock) > Cost(overstock) — hence the asymmetric H(x)"),
        ("Overstock Cost (Holding Cost)","Over-ordering ties up capital (zero-sum: money in inventory can't be used elsewhere) and creates physical liabilities: warehouse space, item degradation, shelf-life expiration.","Holding cost penalty: score ↓ 15% per 10 units above threshold"),
        ("Layout Presentation Separation","Design pattern: the backend computes the data (boolean mask, health scores, aggregates) and the frontend only handles display. Math and UI are decoupled — swapping either doesn't break the other.","Backend: M = df['status'].isin([...]).astype(int)\nFrontend: render df[df.M==1] rows"),
        ("@st.cache_data","Streamlit RAM caching decorator. The decorated function reads from disk exactly once on startup. All subsequent calls are served from background RAM. Eliminates the ~250ms disk I/O on every re-run.","Latency: cache hit <0.1s vs disk read ~250ms\nst.cache_data.clear() → flush RAM, re-read disk"),
        ("Defensive Guard Wall","N=0 / N>0 branching at the top of every page. If no data is loaded (N=0), display a safe informational UI and halt all math operations. Only run formulas when N>0.","if len(df)==0: show safe UI, stop\nelse: run H(x), compute μ, dispatch alerts"),
        ("Row-Wise Mapping","Applying a function to each row of a column vector independently. x=[x1..xn] → h=[H(x1)..H(xn)]. Each SKU gets its own score without any cross-product between rows.","x = stock_vector → h = H(x)  applied element-wise"),
        ("Aggregate Reduction","Reducing a vector to a single scalar by applying an arithmetic operation column-wise. Here: the mean of all health scores gives the store wellness index.","μ = (1/N) × Σ h_i"),
        ("MAD — Mean Absolute Deviation","How much daily demand fluctuates. High MAD = unpredictable product = needs more safety stock.","MAD = average |daily demand − avg demand|"),
        ("Safety Stock","Buffer inventory for demand spikes during supplier lead time.","Safety Stock = Z × MAD × √(Lead Time)  ·  Z=1.65→95%"),
        ("ROP — Reorder Point","Stock level that triggers a new supplier order.","ROP = (Avg Daily Demand × Lead Time) + Safety Stock"),
        ("EMA — Exponential Moving Average","Moving average giving more weight to recent days. Reacts faster than SMA.","EMA_t = α × today + (1−α) × EMA_{t-1}  ·  α=2/(N+1)"),
        ("Holt-Winters","Forecasting tracking level + trend + seasonality simultaneously.","3 components: Level α · Trend β · Seasonality γ"),
        ("RFM — Recency, Frequency, Monetary","Customer scoring: R=how recently, F=how often, M=how much. Score 3–9.","Champion(8-9) · Loyal(6-7) · Potential(4-5) · At Risk(3)"),
        ("Lift (market basket)","How much more likely B is bought when A is in the cart vs random.","Lift = Confidence(A→B) / Support(B)  ·  >1=genuine pair"),
        ("SEO Keyword Density","How often a keyword appears relative to total word count.","Density = (matches / tokens) × 100"),
        ("SEO Sweet Spot","Density 1–3.5%. Human-authored content, crawler trusts the page.","Score = 100  when  1% ≤ density ≤ 3.5%"),
        ("Keyword Stuffing Penalty","Density above 3.5%. Score = max(0, int(100 − (excess × 15))).","excess = density − 3.5% · penalty = excess × 15"),
        ("Sliding Window N-Gram","Scans token list for multi-word phrases by sliding a window of width N.","for i in range(len(tokens)−N+1): check tokens[i:i+N]"),
        ("Stop Words","Common words (the, and, is…) with no SEO signal. Stored as a set for O(1) lookup.","Set membership O(1) vs list scan O(n)"),
        ("Z-Score","Standard deviations from mean. 0=average, ±2=outlier.","Z = (x − μ) / σ"),
        ("Min-Max Scaling","Squeezes values to 0–1.","X' = (x − min) / (max − min)"),
        ("Cyclic Time Encoding","Projects days onto a circle so Sun and Mon are adjacent.","sin=sin(2π×day/7) · cos=cos(2π×day/7)"),
        ("Lag Features","Past values shifted forward so model can see history.","lag_1=yesterday · lag_7=last week"),
        ("First-Order Differencing","Predict daily change not level. Removes trends, achieves stationarity.","ΔY_t = Y_t − Y_{t-1}"),
        ("VIF — Variance Inflation Factor","Detects redundant features. >10 = drop.","VIF = 1/(1−R²)"),
        ("Service Level","Target in-stock probability. Z=1.65→95%, Z=2.05→98%.","Higher level = more safety stock = higher cost"),
    ]
    search = st.text_input("Search","",placeholder="Type any term…")
    filtered = [(t,p,f) for t,p,f in G if search.lower() in t.lower() or search.lower() in p.lower()]
    st.markdown(f"<div style='font-size:11px;color:#1a3050;margin-bottom:12px'>{len(filtered)} terms</div>", unsafe_allow_html=True)
    for term, plain, form in filtered:
        st.markdown(f'<div class="gcard"><div class="gcard-term">{term}</div><div class="gcard-plain">{plain}</div><div class="gcard-formula">{form}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='margin-top:44px;padding-top:12px;border-top:1px solid #0c1c35;color:#0c1c35;font-size:10px;text-align:center'>🧭 Navigare · Retail Analytics · Week 8 · Phase 3 · github.com/SS10-code/Navigare</div>", unsafe_allow_html=True)