"""
dashboard.py — Navigare Retail Analytics  v6
Week 9 · Breeze color scheme · Full filter isolation · Vercel-ready

Color palette (from Breeze design reference):
  Primary:    #423A8E (deep purple)   #00CCCD (teal)
  Supporting: #FFC107 (amber)  #DC3545 (red)  #198754 (green)  #0D6EFD (blue)

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
from itertools import combinations as _comb
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))
from seo_engine import analyse_text, score_density, normalize
from inventory_health import run_inventory_health_pipeline, H

# ─────────────────────────────────────────────────────────────
# AUTH GATE — must run before any other st.* calls
# Uses a simple login form; blocks everything below until authenticated.
# ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;min-height:80vh;flex-direction:column;gap:18px">
      <div style="font-size:52px">🧭</div>
      <div style="font-size:28px;font-weight:800;color:#423A8E">Navigare</div>
      <div style="font-size:14px;color:#6B7280">Retail Analytics · Protected</div>
    </div>""", unsafe_allow_html=True)
    with st.form("login", clear_on_submit=True):
        pw = st.text_input("Password", type="password", placeholder="Enter app password")
        if st.form_submit_button("Log in", use_container_width=True, type="primary"):
            if pw == os.environ.get("APP_PASSWORD", "navigare2025"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()

# ─────────────────────────────────────────────────────────────
# BREEZE COLOR SYSTEM
# ─────────────────────────────────────────────────────────────
C = {
    "purple":  "#423A8E",   # primary — sidebar, headers
    "teal":    "#00CCCD",   # primary — accent, highlights
    "amber":   "#FFC107",   # warning, forecast line
    "red":     "#DC3545",   # danger, crisis alerts
    "green":   "#198754",   # success, healthy
    "blue":    "#0D6EFD",   # info, charts
    "white":   "#FFFFFF",
    "bg":      "#F4F6FB",   # page background (light)
    "card":    "#FFFFFF",   # card background
    "sidebar": "#423A8E",   # sidebar bg
    "text":    "#1C1C3B",   # dark text
    "muted":   "#6B7280",   # muted labels
    "border":  "#E5E7EB",   # card borders
    "dark_bg": "#2D2680",   # sidebar deeper
}

st.set_page_config(
    page_title="Navigare · Retail Analytics",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {{
    background:{C['bg']};
    font-family:'Inter','Segoe UI',sans-serif;
}}
[data-testid="stSidebar"] {{
    background:linear-gradient(160deg,{C['purple']} 0%,{C['dark_bg']} 100%);
    border-right:none;
}}
.main .block-container {{
    padding:1.8rem 2rem 3rem;
    max-width:1360px;
}}
@media (max-width: 768px) {{
    .main .block-container {{ padding:1rem; max-width:100%; }}
    .kpi-grid {{ flex-direction:column; }}
    .kpi-card {{ min-width:100%; }}
}}

/* ── Sidebar nav ── */
div[data-testid="stSidebar"] .stButton>button {{
    width:100%;text-align:left;
    background:rgba(255,255,255,0.06);
    border:none;border-radius:10px;
    color:rgba(255,255,255,0.75);
    padding:10px 14px 10px 16px;
    font-size:13.5px;font-weight:500;
    transition:all .15s;margin-bottom:3px;
    letter-spacing:.2px;
}}
div[data-testid="stSidebar"] .stButton>button:hover {{
    background:rgba(255,255,255,0.15);color:#fff;
    transform:translateX(3px);
}}

/* ── KPI cards ── */
.kpi-grid{{display:flex;gap:14px;margin-bottom:22px;flex-wrap:wrap;}}
.kpi-card{{
    flex:1;min-width:140px;
    background:{C['card']};
    border:1px solid {C['border']};
    border-radius:14px;
    padding:18px 20px;
    box-shadow:0 1px 4px rgba(66,58,142,.06);
    position:relative;overflow:hidden;
}}
.kpi-card::before{{
    content:'';position:absolute;top:0;left:0;
    width:4px;height:100%;
    background:var(--accent,{C['teal']});
    border-radius:4px 0 0 4px;
}}
.kpi-label{{color:{C['muted']};font-size:10.5px;font-weight:600;
    text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;}}
.kpi-value{{color:{C['text']};font-size:26px;font-weight:800;line-height:1.1;}}
.kpi-sub{{color:{C['muted']};font-size:11px;margin-top:3px;}}
.kpi-accent-teal  {{--accent:{C['teal']};}}
.kpi-accent-green {{--accent:{C['green']};}}
.kpi-accent-amber {{--accent:{C['amber']};}}
.kpi-accent-red   {{--accent:{C['red']};}}
.kpi-accent-blue  {{--accent:{C['blue']};}}
.kpi-accent-purple{{--accent:{C['purple']};}}

/* ── Page header ── */
.pg-title{{font-size:22px;font-weight:800;color:{C['text']};margin-bottom:2px;letter-spacing:-.3px;}}
.pg-sub  {{font-size:13.5px;color:{C['muted']};margin-bottom:22px;}}

/* ── Section label ── */
.sec{{
    font-size:10.5px;font-weight:700;color:{C['purple']};
    text-transform:uppercase;letter-spacing:1.2px;
    margin:26px 0 10px;
    display:flex;align-items:center;gap:8px;
}}
.sec::after{{content:'';flex:1;height:1px;background:{C['border']};}}

/* ── Cards ── */
.card{{
    background:{C['card']};border:1px solid {C['border']};
    border-radius:14px;padding:20px;
    box-shadow:0 1px 4px rgba(66,58,142,.06);
    margin-bottom:16px;
}}

/* ── Callout boxes ── */
.callout{{
    border-radius:10px;padding:13px 16px;
    margin:0 0 16px;font-size:13px;line-height:1.7;
}}
.callout-info  {{background:#EEF2FF;border-left:3px solid {C['purple']};color:#3730A3;}}
.callout-info b{{color:{C['purple']};}}
.callout-info code{{background:#C7D2FE;padding:1px 5px;border-radius:4px;font-size:11.5px;color:{C['purple']};}}
.callout-warn  {{background:#FFFBEB;border-left:3px solid {C['amber']};color:#92400E;}}
.callout-good  {{background:#ECFDF5;border-left:3px solid {C['green']};color:#065F46;}}
.callout-danger{{background:#FFF1F2;border-left:3px solid {C['red']};color:#9F1239;}}
.formula{{
    background:#1C1C3B;border-radius:10px;
    padding:13px 18px;font-family:'JetBrains Mono','Courier New',monospace;
    font-size:12.5px;color:#A5F3FC;margin:12px 0;line-height:2;
}}

/* ── Alert cards ── */
.alert-card{{
    display:flex;align-items:center;gap:16px;
    border-radius:12px;padding:14px 18px;margin-bottom:10px;
    background:{C['card']};border:1px solid {C['border']};
}}
.alert-crisis  {{border-left:4px solid {C['red']}  !important;background:#FFF1F2;}}
.alert-critical{{border-left:4px solid #F97316 !important;background:#FFF7ED;}}
.alert-low     {{border-left:4px solid {C['amber']}!important;background:#FFFBEB;}}

/* ── Glossary ── */
.gcard{{
    background:{C['card']};border:1px solid {C['border']};
    border-radius:12px;padding:14px 18px;margin-bottom:10px;
    box-shadow:0 1px 3px rgba(66,58,142,.04);
}}
.gcard-term  {{font-size:13.5px;font-weight:700;color:{C['purple']};margin-bottom:5px;}}
.gcard-plain {{font-size:12.5px;color:{C['text']};margin-bottom:8px;line-height:1.6;}}
.gcard-formula{{font-family:monospace;font-size:11.5px;color:#065F46;
    background:#ECFDF5;border-radius:5px;padding:5px 10px;display:inline-block;}}

/* ── Sidebar text ── */
.sb-logo{{padding:20px 4px 24px;}}
.sb-logo-title{{font-size:20px;font-weight:800;color:#fff;letter-spacing:-.3px;}}
.sb-logo-sub  {{font-size:10.5px;color:rgba(255,255,255,.5);margin-top:2px;}}
.sb-section   {{font-size:10px;font-weight:700;color:rgba(255,255,255,.4);
    text-transform:uppercase;letter-spacing:1px;margin:16px 0 6px 4px;}}
.sb-metric    {{background:rgba(255,255,255,.08);border-radius:10px;padding:12px 14px;margin-bottom:8px;}}
.sb-metric-val{{font-size:20px;font-weight:800;color:#fff;}}
.sb-metric-lbl{{font-size:10px;color:rgba(255,255,255,.55);margin-top:1px;}}

/* ── Divider ── */
hr.nav-div{{border:none;border-top:1px solid rgba(255,255,255,.1);margin:14px 0;}}
</style>
""", unsafe_allow_html=True)

# Plotly theme matching Breeze
PLT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=C["text"]),
)
COLORS = [C["purple"], C["teal"], C["blue"], C["amber"], C["green"], C["red"], "#9333EA", "#F97316"]


# ─────────────────────────────────────────────────────────────
# CACHING LAYER — disk I/O exactly once
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_transactions():
    for path in ["data/clean/unified_transactions.csv", "data/raw/transactions.csv"]:
        if os.path.exists(path):
            df = pd.read_csv(path, parse_dates=["Transaction_Date"])
            if "Store_Type" not in df.columns or df["Store_Type"].isna().all():
                sc = df.get("Source_Currency", pd.Series(dtype=str))
                df["Store_Type"] = sc.map({"BRL":"E-Commerce","GBP":"Brick-and-Mortar"}).fillna("E-Commerce")
            df["Store_Type"] = df["Store_Type"].fillna(
                df.get("Source_Currency", pd.Series(dtype=str)).map({"BRL":"E-Commerce","GBP":"Brick-and-Mortar"}))
            if "Line_Total_USD" not in df.columns and "Line_Total" in df.columns:
                df["Line_Total_USD"] = df["Line_Total"]
            if "Line_Total" not in df.columns and "Line_Total_USD" in df.columns:
                df["Line_Total"] = df["Line_Total_USD"]
            return df
    return pd.DataFrame(columns=["Transaction_Date","Store_Type","Transaction_ID",
                                  "Customer_ID","Product_ID","Line_Total_USD","Line_Total",
                                  "Quantity","Category","Source_Currency"])

@st.cache_data(show_spinner=False)
def load_inventory():
    for path in ["data/clean/inventory_clean.csv","data/raw/inventory.csv"]:
        if os.path.exists(path): return pd.read_csv(path)
    return None

@st.cache_data(show_spinner=False)
def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else None

@st.cache_data(show_spinner=False)
def load_csv_dates(path):
    return pd.read_csv(path, parse_dates=["Date"]) if os.path.exists(path) else None

@st.cache_data(show_spinner=False)
def load_chaos():
    p = "data/clean/chaos_report.json"
    return json.load(open(p)) if os.path.exists(p) else None

@st.cache_data(show_spinner=False)
def load_health(inv_df):
    if inv_df is None or len(inv_df) == 0:
        return None, {"wellness_score":0,"interpretation":"No data","N":0,"status_counts":{}}, pd.DataFrame()
    return run_inventory_health_pipeline(inv_df)

# Filter-aware live metrics
@st.cache_data(show_spinner=False)
def compute_prod(txn, inv_df):
    if txn is None or len(txn)==0 or inv_df is None: return None
    days = max(1,(txn["Transaction_Date"].max()-txn["Transaction_Date"].min()).days+1)
    lc = "Line_Total" if "Line_Total" in txn.columns else "Line_Total_USD"
    t2 = txn.copy(); t2["Product_ID"] = t2["Product_ID"].astype(str)
    i2 = inv_df.copy(); i2["Product_ID"] = i2["Product_ID"].astype(str)
    pt = t2.groupby("Product_ID").agg(
        Total_Units_Sold=("Quantity","sum"),
        Total_Revenue=(lc,"sum"),
        Num_Transactions=("Transaction_ID","nunique")).reset_index()
    df = i2.merge(pt, on="Product_ID", how="left").fillna(0)
    df["Gross_Margin_Pct"] = ((df["Retail_Price"]-df["Cost_Price"])/df["Retail_Price"].replace(0,1)*100).round(1)
    df["Revenue_Per_Day"]  = (df["Total_Revenue"]/days).round(2)
    df["Sell_Through_Pct"] = (df["Total_Units_Sold"]/(df["Total_Units_Sold"]+df["Current_Stock"]).replace(0,np.nan)*100).round(1).fillna(0)
    keep=["Product_ID","Product_Name","Category","Cost_Price","Retail_Price",
          "Gross_Margin_Pct","Current_Stock","Total_Units_Sold","Total_Revenue",
          "Revenue_Per_Day","Sell_Through_Pct"]
    return df[[c for c in keep if c in df.columns]]

@st.cache_data(show_spinner=False)
def compute_rfm(txn):
    if txn is None or len(txn)==0: return None
    lc = "Line_Total" if "Line_Total" in txn.columns else "Line_Total_USD"
    snap = txn["Transaction_Date"].max()+pd.Timedelta(days=1)
    rfm = txn.groupby("Customer_ID").agg(
        Last_Purchase=("Transaction_Date","max"),
        Frequency=("Transaction_ID","nunique"),
        Monetary=(lc,"sum")).reset_index()
    rfm["Recency_Days"] = (snap-rfm["Last_Purchase"]).dt.days
    if len(rfm)<3: rfm["R_Score"]=rfm["F_Score"]=rfm["M_Score"]=2
    else:
        try:
            rfm["R_Score"] = pd.qcut(rfm["Recency_Days"],q=3,labels=[3,2,1]).astype(int)
            rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"),q=3,labels=[1,2,3]).astype(int)
            rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"),q=3,labels=[1,2,3]).astype(int)
        except: rfm["R_Score"]=rfm["F_Score"]=rfm["M_Score"]=2
    rfm["RFM_Score"] = rfm["R_Score"]+rfm["F_Score"]+rfm["M_Score"]
    rfm["Segment"] = rfm["RFM_Score"].apply(lambda s:"Champion" if s>=8 else("Loyal" if s>=6 else("Potential" if s>=4 else"At Risk")))
    rfm["Last_Purchase"] = rfm["Last_Purchase"].dt.date
    rfm["Monetary"] = rfm["Monetary"].round(2)
    return rfm

@st.cache_data(show_spinner=False)
def compute_combo(txn):
    if txn is None or len(txn)==0: return None
    nc = "Product_Name" if "Product_Name" in txn.columns else "Product_ID"
    orders = txn.groupby("Transaction_ID")["Product_ID"].apply(set).reset_index()
    orders.columns = ["Transaction_ID","Products"]
    tot = len(orders)
    if tot==0: return None
    ps={}
    for p in orders["Products"]:
        for x in p: ps[x]=ps.get(x,0)+1
    pc={}
    for p in orders[orders["Products"].apply(len)>=2]["Products"]:
        for pair in _comb(sorted(p),2): pc[pair]=pc.get(pair,0)+1
    res=[]
    for (a,b),cnt in pc.items():
        sup=cnt/tot
        if sup<0.02: continue
        cf=cnt/ps.get(a,1); sb=ps.get(b,1)/tot
        res.append({"Product_A_ID":a,"Product_B_ID":b,"Co_Occurrences":cnt,
                    "Support":round(sup,4),"Confidence_AB":round(cf,4),"Lift":round(cf/sb if sb>0 else 0,3)})
    if not res: return None
    df = pd.DataFrame(res).sort_values("Lift",ascending=False).head(30)
    nm = txn[["Product_ID",nc]].drop_duplicates().set_index("Product_ID")[nc]
    df["Product_A"]=df["Product_A_ID"].map(nm); df["Product_B"]=df["Product_B_ID"].map(nm)
    df["Pair_Label"]=df["Product_A"].astype(str)+"  +  "+df["Product_B"].astype(str)
    return df[["Pair_Label","Product_A","Product_B","Co_Occurrences","Support","Confidence_AB","Lift"]].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
with st.spinner(""):
    txn_df   = load_transactions()
    inv_raw  = load_inventory()
    inv_met  = load_csv("data/clean/inventory_metrics.csv")
    feat_df  = load_csv_dates("data/clean/features.csv")
    ema_df   = load_csv_dates("data/clean/ema_forecast.csv")
    adf_df   = load_csv("data/clean/adf_results.csv")
    vif_df   = load_csv("data/clean/vif_results.csv")
    chaos    = load_chaos()
    health_df, wellness, critical_df = load_health(inv_raw)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sb-logo">
      <div class="sb-logo-title">🧭 Navigare</div>
      <div class="sb-logo-sub">Retail Analytics · Phase 4</div>
    </div>""", unsafe_allow_html=True)

    PAGES = {
        "📊  Overview":            "overview",
        "📦  Inventory Health":    "inventory",
        "🛒  What Sells Together": "combo",
        "👥  Customer Segments":   "customers",
        "📈  Sales Forecast":      "forecast",
        "🔍  SEO Auditor":         "seo",
        "🔬  Under the Hood":      "features",
        "📤  Upload Data":         "upload",
        "💰  Profit Optimizer":    "profit",
        "🚀  Onboarding":          "onboarding",
        "📖  Glossary":            "glossary",
    }
    if "page" not in st.session_state: st.session_state.page = "overview"
    st.markdown('<div class="sb-section">Navigation</div>', unsafe_allow_html=True)
    for label, key in PAGES.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key; st.rerun()

    st.markdown('<hr class="nav-div">', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Filters</div>', unsafe_allow_html=True)

    store_opts = ["All Stores"] + sorted(txn_df["Store_Type"].dropna().unique().tolist())
    sel_store  = st.selectbox("Store", store_opts, label_visibility="collapsed")
    d_min = txn_df["Transaction_Date"].min().date()
    d_max = txn_df["Transaction_Date"].max().date()
    dr    = st.date_input("", (d_min, d_max), min_value=d_min, max_value=d_max,
                          label_visibility="collapsed")

    st.markdown('<hr class="nav-div">', unsafe_allow_html=True)

    # Store wellness in sidebar — smaller number as per session notes
    ws    = wellness.get("wellness_score", 0)
    wint  = wellness.get("interpretation","—")
    wc    = C["green"] if ws>=70 else (C["amber"] if ws>=50 else C["red"])
    nc    = len(critical_df) if critical_df is not None else 0
    st.markdown(f"""
    <div class="sb-metric">
      <div style="font-size:9.5px;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px">Store Wellness</div>
      <div style="font-size:24px;font-weight:800;color:{wc};line-height:1">{ws}/100</div>
      <div style="font-size:10.5px;color:rgba(255,255,255,.55);margin-top:2px">{wint}</div>
    </div>""", unsafe_allow_html=True)
    if nc > 0:
        st.markdown(f"""
        <div style="background:rgba(220,53,69,.15);border:1px solid rgba(220,53,69,.4);
            border-radius:10px;padding:10px 14px;margin-bottom:8px">
          <div style="font-size:11px;font-weight:700;color:#FCA5A5">🚨 {nc} Priority Alert{"s" if nc!=1 else ""}</div>
          <div style="font-size:9.5px;color:rgba(255,255,255,.45);margin-top:1px">SKUs needing action</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="nav-div">', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Cache</div>', unsafe_allow_html=True)
    if st.button("↻  Refresh Data", use_container_width=True,
                 help="Clears RAM, re-reads all CSVs from disk"):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div style="font-size:10px;color:rgba(255,255,255,.3);margin-top:4px;padding-left:4px">Cached in RAM · click after updating files</div>', unsafe_allow_html=True)


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

# Live filter-aware metrics
prod_df  = compute_prod(filt, inv_raw)
rfm_df   = compute_rfm(filt)
combo_df = compute_combo(filt)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def kpis(metrics):
    accents = [C["teal"],C["green"],C["purple"],C["amber"],C["blue"],C["red"]]
    html = '<div class="kpi-grid">'
    for i,(lbl,val,sub) in enumerate(metrics):
        a = accents[i % len(accents)]
        html += f'<div class="kpi-card" style="--accent:{a}"><div class="kpi-label">{lbl}</div><div class="kpi-value">{val}</div><div class="kpi-sub">{sub}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)

def info(t):
    st.markdown(f'<div class="callout callout-info">{t}</div>', unsafe_allow_html=True)

def warn(t):
    st.markdown(f'<div class="callout callout-warn">{t}</div>', unsafe_allow_html=True)

def good(t):
    st.markdown(f'<div class="callout callout-good">{t}</div>', unsafe_allow_html=True)

def danger(t):
    st.markdown(f'<div class="callout callout-danger">{t}</div>', unsafe_allow_html=True)

def fml(t):
    st.markdown(f'<div class="formula">{t}</div>', unsafe_allow_html=True)

def guard(df, name="data"):
    if df is None or (hasattr(df,"__len__") and len(df)==0):
        st.info(f"No {name} found. Run the pipeline, then click ↻ Refresh Data.")
        return False
    return True

STATUS_COLOR = {
    "CRISIS":C["red"],"CRITICAL":"#F97316","LOW":C["amber"],
    "WARNING":"#84cc16","HEALTHY":C["green"],"OPTIMAL":C["teal"],"OVERSTOCK":C["purple"]
}


# ═════════════════════════════════════════════════════════════
# OVERVIEW
# ═════════════════════════════════════════════════════════════
if st.session_state.page == "overview":
    st.markdown('<div class="pg-title">📊 Store Overview</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">Showing data for <b>{sel_store}</b> · {dr[0] if len(dr)>0 else d_min} → {dr[1] if len(dr)>1 else d_max}</div>', unsafe_allow_html=True)

    if not guard(filt, "transactions"): st.stop()
    rev    = filt["Line_Total_USD"].sum()
    orders = filt["Transaction_ID"].nunique()
    aov    = filt.groupby("Transaction_ID")["Line_Total_USD"].sum().mean() if orders>0 else 0
    kpis([
        ("Total Revenue",     f"${rev:,.0f}",   "all channels"),
        ("Total Orders",      f"{orders:,}",     "transactions"),
        ("Avg Order Value",   f"${aov:,.2f}",    "per checkout"),
        ("Store Wellness",    f"{ws}/100",        wint),
        ("Priority Alerts",   f"{nc}",            "need action now"),
    ])

    c1, c2 = st.columns([3,1])
    with c1:
        sec("Revenue Over Time")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ds.index, y=ds.values, name="Daily Revenue",
            fill="tozeroy",
            fillcolor=f"rgba(67,58,142,0.08)",
            line=dict(color=C["purple"], width=2.5)))
        roll = ds.rolling(7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=roll.index, y=roll.values, name="7-day avg",
            line=dict(color=C["teal"], width=2, dash="dash")))
        fig.update_layout(**PLT, height=300, hovermode="x unified",
            margin=dict(l=0,r=0,t=8,b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(gridcolor=C["border"], tickprefix="$"),
            xaxis=dict(gridcolor=C["border"]))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        if sel_store == "All Stores":
            sec("Channel Split")
            rv = filt.groupby("Store_Type")["Line_Total_USD"].sum().reset_index()
            fig_p = px.pie(rv, values="Line_Total_USD", names="Store_Type",
                color_discrete_sequence=[C["purple"], C["teal"]], hole=0.6)
            fig_p.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=0,b=0),
                legend=dict(orientation="h", y=-0.15))
            fig_p.update_traces(textinfo="percent", textfont_size=11)
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            sec("By Category")
            if "Category" in filt.columns:
                rv = filt.groupby("Category")["Line_Total_USD"].sum().reset_index()
                fig_p = px.pie(rv, values="Line_Total_USD", names="Category",
                    color_discrete_sequence=COLORS, hole=0.6)
                fig_p.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=0,b=0),
                    legend=dict(orientation="h", y=-0.15))
                fig_p.update_traces(textinfo="percent", textfont_size=10)
                st.plotly_chart(fig_p, use_container_width=True)

    if prod_df is not None and len(prod_df) > 0:
        sec("Top Products by Revenue")
        top = prod_df.nlargest(10,"Total_Revenue")
        fig_b = go.Figure(go.Bar(
            x=top["Total_Revenue"], y=top["Product_Name"],
            orientation="h",
            marker=dict(color=COLORS*3, colorscale=None),
            text=[f"${v:,.0f}" for v in top["Total_Revenue"]],
            textposition="outside"))
        fig_b.update_layout(**PLT, height=320, margin=dict(l=0,r=60,t=8,b=0),
            xaxis=dict(tickprefix="$", gridcolor=C["border"]),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_b, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# INVENTORY HEALTH
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "inventory":
    st.markdown('<div class="pg-title">📦 Inventory Health</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">H(x) applied to every SKU · Store wellness index μ · Priority alert dispatch</div>', unsafe_allow_html=True)

    if not guard(inv_raw,"inventory") or not guard(health_df,"health scores"): st.stop()

    sc = wellness.get("status_counts",{})
    kpis([
        ("Wellness Index μ",    f"{ws}/100",                        wint),
        ("SKUs Tracked",        f"{wellness.get('N',0)}",           "products"),
        ("🔴 Crisis + Critical", f"{sc.get('CRISIS',0)+sc.get('CRITICAL',0)}", "expedite now"),
        ("🟡 Low Stock",         f"{sc.get('LOW',0)}",              "order now"),
        ("🟢 Healthy + Optimal", f"{sc.get('HEALTHY',0)+sc.get('OPTIMAL',0)}", "no action"),
    ])

    info(f"""<b>H(x) — Asymmetric Health Function</b><br>
    Applied row-wise to each SKU's stock count → score 0–100.
    Asymmetric because stockouts are more damaging than overstock.
    <b>Store Wellness μ = (1/N) × Σ H(xᵢ) = {ws}/100</b> — mean across all {wellness.get('N',0)} SKUs.""")

    # Wellness gauge + health bars side by side
    g1, g2 = st.columns([1,3])
    with g1:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ws,
            gauge=dict(
                axis=dict(range=[0,100]),
                bar=dict(color=wc, thickness=0.3),
                steps=[
                    dict(range=[0,30],  color="#FEE2E2"),
                    dict(range=[30,60], color="#FEF9C3"),
                    dict(range=[60,80], color="#DCFCE7"),
                    dict(range=[80,100],color="#D1FAE5"),
                ],
                threshold=dict(line=dict(color=C["purple"],width=3), thickness=0.8, value=70)
            ),
            number=dict(suffix="/100", font=dict(color=wc, size=28)),
        ))
        fig_g.update_layout(**PLT, height=250, margin=dict(l=20,r=20,t=20,b=10))
        st.plotly_chart(fig_g, use_container_width=True)

    with g2:
        hdf = health_df.sort_values("Health_Score")
        nc_ = "Product_Name" if "Product_Name" in hdf.columns else "Product_ID"
        fig_h = go.Figure(go.Bar(
            x=hdf["Health_Score"], y=hdf[nc_],
            orientation="h",
            marker_color=hdf["Health_Color"].tolist(),
            text=[f"{v}" for v in hdf["Health_Score"]],
            textposition="outside"))
        fig_h.add_vline(x=70, line_color=C["border"], line_dash="dash", line_width=1.5,
                        annotation_text="Healthy threshold",
                        annotation_font_color=C["muted"], annotation_font_size=10)
        fig_h.update_layout(**PLT, height=500, margin=dict(l=0,r=50,t=10,b=0),
            xaxis=dict(range=[0,115], gridcolor=C["border"]),
            yaxis=dict(tickfont=dict(size=10), gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_h, use_container_width=True)

    # Priority alerts
    sec("🚨 Priority Alert Dispatch")
    info("<b>Boolean Mask M_i = 1</b> if status ∈ {CRISIS, CRITICAL, LOW} · Layout Presentation Separation: backend computes mask, UI renders M=1 rows only.")

    if critical_df is None or len(critical_df) == 0:
        good("✅ No priority alerts — all SKUs above LOW threshold.")
    else:
        nc_ = "Product_Name" if "Product_Name" in critical_df.columns else "Product_ID"
        for status in ["CRISIS","CRITICAL","LOW"]:
            grp = critical_df[critical_df["Health_Status"] == status]
            if not len(grp): continue
            sec(f"{status} — {len(grp)} SKU{'s' if len(grp)>1 else ''}")
            for _, row in grp.iterrows():
                sc_ = STATUS_COLOR.get(status, C["muted"])
                st.markdown(f"""
                <div class="alert-card alert-{status.lower()}">
                  <div style="font-size:32px;font-weight:900;color:{sc_};min-width:52px;text-align:center">{row.get('Health_Score',0)}</div>
                  <div style="flex:1">
                    <div style="font-weight:700;color:{C['text']};font-size:14px">{row.get(nc_,'—')}</div>
                    <div style="font-size:12px;color:{C['muted']};margin-top:2px">{row.get('Health_Explanation','')}</div>
                  </div>
                  <div style="text-align:center;min-width:52px">
                    <div style="font-size:22px;font-weight:800;color:{C['text']}">{int(row.get('Current_Stock',0))}</div>
                    <div style="font-size:10px;color:{C['muted']}">units</div>
                  </div>
                </div>""", unsafe_allow_html=True)

    # ROP chart
    if inv_met is not None and len(inv_met)>0:
        sec("Current Stock vs Reorder Point")
        fig_rop = go.Figure()
        status_list = health_df["Health_Status"].tolist() if health_df is not None and "Health_Status" in health_df.columns else ["HEALTHY"]*len(inv_met)
        colors_rop  = [STATUS_COLOR.get(s, C["blue"]) for s in status_list]
        fig_rop.add_trace(go.Bar(name="Current Stock",
            x=inv_met["Product_Name"], y=inv_met["Current_Stock"],
            marker_color=colors_rop, opacity=0.85))
        fig_rop.add_trace(go.Scatter(name="Reorder Point",
            x=inv_met["Product_Name"], y=inv_met["ROP"],
            mode="markers", marker=dict(symbol="line-ew", size=14,
            color=C["red"], line=dict(width=2.5, color=C["red"]))))
        fig_rop.add_trace(go.Scatter(name="Safety Stock",
            x=inv_met["Product_Name"], y=inv_met["Safety_Stock"],
            mode="lines", line=dict(color=C["amber"], width=1.5, dash="dot")))
        fig_rop.update_layout(**PLT, height=360, hovermode="x", barmode="overlay",
            margin=dict(l=0,r=0,t=8,b=0),
            yaxis=dict(gridcolor=C["border"]),
            xaxis=dict(tickangle=-40, tickfont=dict(size=9), gridcolor="rgba(0,0,0,0)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_rop, use_container_width=True)
        warn("Products where the bar falls <b>below</b> the red marker need to be ordered today.")

    # H(x) curve
    sec("H(x) Asymmetric Scoring Curve")
    x_r = np.arange(0,151,1)
    y_r = [H(float(x))["score"] for x in x_r]
    y_c = [STATUS_COLOR.get(H(float(x))["status"], C["blue"]) for x in x_r]
    fig_hx = go.Figure()
    fig_hx.add_trace(go.Scatter(x=x_r, y=y_r, mode="lines",
        line=dict(color=C["purple"], width=3), name="H(x)"))
    fig_hx.add_scatter(x=x_r, y=y_r, mode="markers",
        marker=dict(color=y_c, size=3.5), showlegend=False)
    fig_hx.add_vline(x=10,  line_color=C["border"], line_dash="dash", line_width=1,
                     annotation_text="ROP=10",       annotation_font_color=C["muted"], annotation_font_size=10)
    fig_hx.add_vline(x=100, line_color=C["border"], line_dash="dash", line_width=1,
                     annotation_text="Overstock=100",annotation_font_color=C["muted"], annotation_font_size=10)
    fig_hx.update_layout(**PLT, height=260, margin=dict(l=0,r=0,t=10,b=0),
        xaxis=dict(title="Current Stock Units", gridcolor=C["border"]),
        yaxis=dict(title="H(x) Score", gridcolor=C["border"]))
    st.plotly_chart(fig_hx, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# WHAT SELLS TOGETHER
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "combo":
    st.markdown('<div class="pg-title">🛒 What Sells Together</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">Market basket analysis for <b>{sel_store}</b> — based on {filt["Transaction_ID"].nunique():,} orders</div>', unsafe_allow_html=True)
    if not guard(combo_df,"combo pairs"): st.stop()

    info("""<b>Lift > 1</b> means the pair is genuinely associated, not just popular.
    <b>Support</b> = % of all orders with this pair.
    <b>Confidence</b> = if A is bought, probability B is too.
    With {n} SKUs we check {p} pairs directly. At 500+ SKUs, switch to FP-Growth.""".format(
        n=len(filt["Product_ID"].unique()), p=len(filt["Product_ID"].unique())*(len(filt["Product_ID"].unique())-1)//2))

    kpis([
        ("Pairs Found",    f"{len(combo_df)}",                          "above threshold"),
        ("Top Lift",       f"{combo_df['Lift'].max():.2f}×",            "strongest link"),
        ("Avg Confidence", f"{combo_df['Confidence_AB'].mean():.1%}",   "A → B"),
        ("Orders Scanned", f"{filt['Transaction_ID'].nunique():,}",      "baskets"),
    ])

    sec("Strongest Pairs (ranked by Lift)")
    top = combo_df.head(15)
    fig_c = go.Figure(go.Bar(
        x=top["Lift"], y=top["Pair_Label"], orientation="h",
        marker=dict(color=[C["green"] if v>=2 else (C["teal"] if v>=1.5 else C["purple"]) for v in top["Lift"]]),
        text=[f"{v:.2f}×" for v in top["Lift"]], textposition="outside"))
    fig_c.add_vline(x=1, line_color=C["border"], line_dash="dash", line_width=1.5)
    fig_c.update_layout(**PLT, height=460, margin=dict(l=0,r=60,t=8,b=0),
        xaxis=dict(title="Lift", gridcolor=C["border"]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_c, use_container_width=True)

    sec("Full Pair Table")
    d = combo_df.copy()
    d["Support"]       = d["Support"].apply(lambda x: f"{x:.1%}")
    d["Confidence_AB"] = d["Confidence_AB"].apply(lambda x: f"{x:.1%}")
    d["Lift"]          = d["Lift"].apply(lambda x: f"{x:.2f}×")
    d.columns = ["Pair","Product A","Product B","Orders Together","Support","Confidence (A→B)","Lift"]
    st.dataframe(d[["Pair","Orders Together","Support","Confidence (A→B)","Lift"]],
                 use_container_width=True, height=300)


# ═════════════════════════════════════════════════════════════
# CUSTOMERS
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "customers":
    st.markdown('<div class="pg-title">👥 Customer Segments</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">RFM scoring for <b>{sel_store}</b> customers</div>', unsafe_allow_html=True)
    if not guard(rfm_df,"customer data"): st.stop()

    info("""<b>Recency</b> — bought recently? 3=yes ·
    <b>Frequency</b> — how often? 3=frequent ·
    <b>Monetary</b> — how much? 3=high spender ·
    Score 3–9 → <b>Champion</b> (8–9) · <b>Loyal</b> (6–7) · <b>Potential</b> (4–5) · <b>At Risk</b> (3)""")

    sc_ = rfm_df["Segment"].value_counts() if "Segment" in rfm_df.columns else pd.Series()
    kpis([
        ("Customers",   f"{rfm_df['Customer_ID'].nunique()}",       sel_store),
        ("Champions",   f"{sc_.get('Champion',0)}",                 "top buyers"),
        ("Loyal",       f"{sc_.get('Loyal',0)}",                    "consistent"),
        ("At Risk",     f"{sc_.get('At Risk',0)}",                  "need attention"),
        ("Avg Spend",   f"${rfm_df['Monetary'].mean():,.2f}",        "per customer"),
    ])

    SCOLS = {"Champion":C["green"],"Loyal":C["teal"],"Potential":C["blue"],"At Risk":C["red"]}
    sr = rfm_df.groupby("Segment")["Monetary"].sum() if "Segment" in rfm_df.columns else pd.Series()

    c1,c2 = st.columns(2)
    with c1:
        sec("Customers by Segment")
        fig_s = go.Figure(go.Bar(x=sc_.index, y=sc_.values,
            marker_color=[SCOLS.get(s,C["blue"]) for s in sc_.index],
            text=sc_.values, textposition="outside"))
        fig_s.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=8,b=0),
            yaxis=dict(gridcolor=C["border"]), xaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_s, use_container_width=True)
    with c2:
        sec("Revenue by Segment")
        fig_r = go.Figure(go.Bar(x=sr.index, y=sr.values,
            marker_color=[SCOLS.get(s,C["blue"]) for s in sr.index],
            text=[f"${v:,.0f}" for v in sr.values], textposition="outside"))
        fig_r.update_layout(**PLT, height=280, margin=dict(l=0,r=0,t=8,b=0),
            yaxis=dict(gridcolor=C["border"],tickprefix="$"), xaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_r, use_container_width=True)

    sec("Recency vs Total Spend")
    fig_sc = px.scatter(rfm_df, x="Recency_Days", y="Monetary", color="Segment",
        size="Frequency", hover_data=["Customer_ID"],
        color_discrete_map=SCOLS,
        labels={"Recency_Days":"Days Since Last Purchase","Monetary":"Total Spend ($)"})
    fig_sc.update_layout(**PLT, height=360, margin=dict(l=0,r=0,t=8,b=0),
        yaxis=dict(gridcolor=C["border"],tickprefix="$"),
        xaxis=dict(gridcolor=C["border"]))
    st.plotly_chart(fig_sc, use_container_width=True)

    sec("Customer Table")
    d = rfm_df[["Customer_ID","Last_Purchase","Recency_Days","Frequency","Monetary","RFM_Score","Segment"]].copy()
    d["Monetary"] = d["Monetary"].apply(lambda x:f"${x:,.2f}")
    st.dataframe(d, use_container_width=True, height=320)


# ═════════════════════════════════════════════════════════════
# FORECAST
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "forecast":
    st.markdown('<div class="pg-title">📈 Sales Forecast</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pg-sub">Three forecasting models for <b>{sel_store}</b></div>', unsafe_allow_html=True)
    if not guard(filt,"transactions"): st.stop()

    c1,c2,c3,c4 = st.columns(4)
    sw = c1.slider("Smoothing window",3,30,7)
    ew = c2.slider("EMA window",3,30,7)
    sp = c3.number_input("Seasonal period",2,30,7)
    fd = c4.slider("Forecast days",7,60,14)
    al = 2/(ew+1)

    e1,e2,e3 = st.columns(3)
    with e1: info(f"<b>Simple Moving Average</b><br>Last {sw} days averaged equally. Smooth, but lags behind change.")
    with e2: info(f"<b>Weighted Avg (EMA)</b><br>Recent days count more. α={al:.3f} weights today vs yesterday.")
    with e3: info(f"<b>Holt-Winters</b><br>Tracks level + trend + {sp}-day seasonality simultaneously.")

    sma_s = ds.rolling(sw,min_periods=1).mean()
    ema_s = ds.ewm(span=ew,adjust=False).mean()
    hw_ok = False
    try:
        hw = ExponentialSmoothing(ds,trend="add",seasonal="add",
            seasonal_periods=int(sp),initialization_method="estimated").fit(optimized=True)
        hw_fit = hw.fittedvalues
        fc_idx = pd.date_range(ds.index[-1]+pd.Timedelta(days=1),periods=fd,freq="D")
        hw_fc  = pd.Series(hw.forecast(fd).values,index=fc_idx)
        hw_ok  = True
    except Exception as e:
        warn(f"Holt-Winters couldn't fit: {str(e)[:120]}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ds.index, y=ds.values, name="Actual",
        line=dict(color=C["border"],width=1), opacity=0.9))
    fig.add_trace(go.Scatter(x=sma_s.index, y=sma_s.values, name=f"SMA-{sw}",
        line=dict(color=C["amber"],width=2,dash="dash")))
    fig.add_trace(go.Scatter(x=ema_s.index, y=ema_s.values, name=f"EMA-{ew} (α={al:.2f})",
        line=dict(color=C["teal"],width=2.5)))
    if hw_ok:
        fig.add_trace(go.Scatter(x=hw_fit.index, y=hw_fit.values, name="HW Fitted",
            line=dict(color=C["green"],width=2),opacity=0.85))
        fig.add_trace(go.Scatter(x=hw_fc.index, y=hw_fc.values,
            name=f"HW Forecast +{fd}d",
            line=dict(color=C["purple"],width=2.5,dash="dot"),
            fill="tozeroy",fillcolor=f"rgba(67,58,142,0.05)"))
        fig.add_vline(x=str(ds.index[-1]),line_color=C["muted"],line_dash="dash",line_width=1,
            annotation_text="  Today",annotation_font_color=C["muted"],annotation_font_size=10)
    fig.update_layout(**PLT,height=400,hovermode="x unified",margin=dict(l=0,r=0,t=10,b=0),
        yaxis=dict(gridcolor=C["border"],tickprefix="$"),xaxis=dict(gridcolor=C["border"]),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig,use_container_width=True)

    if ema_df is not None:
        sec("14-Day EMA Projection")
        tc1,tc2 = st.columns([2,1])
        with tc1:
            fig_e = go.Figure()
            fig_e.add_trace(go.Scatter(x=ds.index[-30:],y=ds.values[-30:],
                name="Last 30 days",line=dict(color=C["purple"],width=2),
                fill="tozeroy",fillcolor=f"rgba(67,58,142,0.05)"))
            fig_e.add_trace(go.Scatter(x=ema_df["Date"],y=ema_df["EMA_Forecast"],
                name="Forecast",line=dict(color=C["teal"],width=2.5,dash="dot"),
                fill="tozeroy",fillcolor=f"rgba(0,204,205,0.05)"))
            fig_e.update_layout(**PLT,height=240,hovermode="x unified",margin=dict(l=0,r=0,t=8,b=0),
                yaxis=dict(gridcolor=C["border"],tickprefix="$"),xaxis=dict(gridcolor=C["border"]))
            st.plotly_chart(fig_e,use_container_width=True)
        with tc2:
            d = ema_df[["Date","Day_Ahead","EMA_Forecast"]].copy()
            d["Date"] = pd.to_datetime(d["Date"]).dt.strftime("%b %d")
            d["EMA_Forecast"] = d["EMA_Forecast"].apply(lambda x:f"${x:,.2f}")
            d.columns = ["Date","Day","Forecast"]
            st.dataframe(d,use_container_width=True,height=240)

    if hw_ok:
        sec("Model Accuracy (avg daily error)")
        act    = ds.reindex(hw_fit.index).fillna(0)
        hw_mae = (act-hw_fit).abs().mean()
        sma_al = sma_s.reindex(ds.index).ffill(); sma_mae=(ds-sma_al).abs().mean()
        ema_al = ema_s.reindex(ds.index);         ema_mae=(ds-ema_al).abs().mean()
        winner = min([("SMA",sma_mae),("EMA",ema_mae),("Holt-Winters",hw_mae)],key=lambda x:x[1])
        ac1,ac2,ac3 = st.columns(3)
        for col,nm,mae in [(ac1,"SMA",sma_mae),(ac2,"EMA",ema_mae),(ac3,"Holt-Winters",hw_mae)]:
            badge = " 🏆" if nm==winner[0] else ""
            col.metric(f"{nm}{badge}",f"${mae:.2f}/day",
                delta="most accurate" if nm==winner[0] else None,
                delta_color="normal" if nm==winner[0] else "off")


# ═════════════════════════════════════════════════════════════
# SEO AUDITOR
# ═════════════════════════════════════════════════════════════
elif st.session_state.page == "seo":
    st.markdown('<div class="pg-title">🔍 SEO Auditor</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Paste any web copy · check keyword density · get an instant score. No API keys, no scraping.</div>', unsafe_allow_html=True)

    info("""<b>How it works:</b>
    Lowercase → strip punctuation → tokenise → sliding window N-gram scan → piecewise density score<br>
    <b>&lt;1%</b> = 50 (under-optimized) ·
    <b>1–3.5%</b> = 100 (sweet spot) ·
    <b>&gt;3.5%</b> = max(0, 100−(excess×15)) (stuffing penalty)""")

    col_t, col_k = st.columns([2,1])
    with col_t:
        sec("Your Web Copy")
        body = st.text_area("",height=240,
            placeholder="Paste your homepage, product page, or Google Business listing here…",
            label_visibility="collapsed")
        if body.strip():
            st.caption(f"Token count: {len(normalize(body))}")
    with col_k:
        sec("Target Keywords (one per line)")
        kws = st.text_area("","bakery near me\nfresh bread\ncustom birthday cake\nartisan bakery\nsourdough loaf",
            height=160,label_visibility="collapsed")
        nosw = st.checkbox("Remove stop-words from count",value=False)

    if st.button("▶  Run SEO Audit",type="primary"):
        if not body.strip():
            st.error("Paste web copy first.")
        else:
            keywords = [k.strip() for k in kws.strip().splitlines() if k.strip()]
            with st.spinner("Analysing…"):
                report = analyse_text(body,keywords,remove_stopwords=nosw)
            if "error" in report:
                st.error(report["error"])
            else:
                h = report["page_health_score"]
                hc = C["green"] if h>=90 else (C["teal"] if h>=70 else (C["amber"] if h>=50 else C["red"]))
                kpis([
                    ("Page Health",  f"{h}/100",                    "Excellent" if h>=90 else ("Good" if h>=70 else ("Needs Work" if h>=50 else "Poor"))),
                    ("Word Count",   f"{report['token_count']}",    "tokens"),
                    ("Keywords",     f"{report['keyword_count']}",  "phrases checked"),
                ])
                sec("Keyword Results")
                r_list = report["results"]
                kn = [r["keyword"] for r in r_list if "score" in r]
                ks = [r["score"]   for r in r_list if "score" in r]
                kd = [r["density_pct"] for r in r_list if "score" in r]
                sv = [r["severity"]    for r in r_list if "score" in r]
                smap = {"none":C["green"],"low":"#86efac","medium":C["amber"],"high":"#F97316","critical":C["red"]}
                if kn:
                    fig_kw = go.Figure()
                    fig_kw.add_trace(go.Bar(name="Score",x=kn,y=ks,
                        marker_color=[smap.get(s,C["blue"]) for s in sv],
                        text=[f"{v}" for v in ks],textposition="outside",yaxis="y1"))
                    fig_kw.add_trace(go.Scatter(name="Density %",x=kn,y=kd,
                        mode="lines+markers",line=dict(color=C["amber"],width=2),
                        marker=dict(size=8),yaxis="y2"))
                    fig_kw.add_hrect(y0=1,y1=3.5,fillcolor=f"rgba(25,135,84,0.05)",
                        line_width=0,yref="y2",annotation_text="Sweet spot 1–3.5%",
                        annotation_font_color=C["green"],annotation_font_size=10)
                    fig_kw.update_layout(**PLT,height=320,hovermode="x unified",margin=dict(l=0,r=0,t=10,b=0),
                        yaxis=dict(title="SEO Score",range=[0,115],gridcolor=C["border"]),
                        yaxis2=dict(title="Density %",overlaying="y",side="right",
                                    range=[0,max(kd)*2.2+1] if kd else [0,10],gridcolor="rgba(0,0,0,0)"),
                        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                    st.plotly_chart(fig_kw,use_container_width=True)

                for r in r_list:
                    if "error" in r: warn(f"'{r['keyword']}' — {r['error']}"); continue
                    sev = r["severity"]; icon = "✅" if sev=="none" else ("⚠️" if sev in ["low","medium"] else "🔴")
                    with st.expander(f"{icon}  \"{r['keyword']}\"  ·  {r['score']}/100  ·  {r['zone']}"):
                        m1,m2,m3,m4 = st.columns(4)
                        m1.metric("Score",f"{r['score']}/100")
                        m2.metric("Matches",r["match_count"])
                        m3.metric("Density",f"{r['density_pct']:.2f}%")
                        m4.metric("N-Gram",f"{r['n_gram_size']}w")
                        box = "good" if sev=="none" else ("danger" if sev in ["critical","high"] else "warn")
                        st.markdown(f'<div class="callout callout-{box}">{r["explanation"]}</div>',unsafe_allow_html=True)

                sec("Scoring Zone Curve")
                x_r = np.linspace(0,12,300)
                y_r = [score_density(float(x))["score"] for x in x_r]
                fig_z = go.Figure()
                fig_z.add_trace(go.Scatter(x=x_r,y=y_r,line=dict(color=C["purple"],width=3),fill="tozeroy",
                    fillcolor=f"rgba(67,58,142,0.08)",name="Score"))
                fig_z.add_vrect(x0=0,x1=1,fillcolor=f"rgba(220,53,69,.06)",line_width=0,
                    annotation_text="Under",annotation_font_color=C["red"],annotation_font_size=10)
                fig_z.add_vrect(x0=1,x1=3.5,fillcolor=f"rgba(25,135,84,.06)",line_width=0,
                    annotation_text="Sweet Spot",annotation_font_color=C["green"],annotation_font_size=10)
                fig_z.add_vrect(x0=3.5,x1=12,fillcolor=f"rgba(255,193,7,.05)",line_width=0,
                    annotation_text="Penalty",annotation_font_color=C["amber"],annotation_font_size=10)
                fig_z.update_layout(**PLT,height=260,margin=dict(l=0,r=0,t=30,b=0),
                    xaxis=dict(title="Density (%)",gridcolor=C["border"]),
                    yaxis=dict(title="Score",gridcolor=C["border"]))
                st.plotly_chart(fig_z,use_container_width=True)


# ═════════════════════════════════════════════════════════════
# UNDER THE HOOD
# ═════════════════════════════════════════════════════════════
    elif st.session_state.page == "features":
        st.markdown('<div class="pg-title">🔬 Under the Hood</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">The math behind the forecasting features. See the Glossary for plain-English definitions.</div>', unsafe_allow_html=True)
        if not guard(feat_df,"feature data"): st.stop()
        sel = st.selectbox("Jump to",["Normalisation (Z-Score & Min-Max)","Cyclic Time Encoding",
                                       "Lag Features (Memory)","Stationarity & Differencing","VIF (Feature Redundancy)"])
        st.markdown(f'<hr style="border-color:{C["border"]};margin:16px 0">', unsafe_allow_html=True)

        if "Normalisation" in sel:
            info("Normalisation removes scale bias so models don't treat $5,000 revenue days as more important than day-of-week (0–6) just because the numbers are bigger.")
            fml("Z = (x − μ) / σ              ← Z-Score: centres at 0, units = std deviations\nX' = (x − min) / (max − min)  ← Min-Max: squeezes to [0, 1]")
            mu=feat_df["Revenue_USD"].mean();sig=feat_df["Revenue_USD"].std();outs=(feat_df["Revenue_ZScore"].abs()>2).sum()
            st.columns(3)[0].metric("Mean",f"${mu:,.2f}")
            st.columns(3)[1].metric("Std Dev",f"${sig:,.2f}")
            st.columns(3)[2].metric("Outlier days |z|>2",str(outs))
            fig_n=make_subplots(rows=2,cols=1,subplot_titles=("Z-Score","Min-Max"),vertical_spacing=0.14)
            fig_n.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_ZScore"],
                line=dict(color=C["purple"],width=1.5),fill="tozeroy",fillcolor=f"rgba(67,58,142,.07)"),row=1,col=1)
            for lvl,col in [(2,C["red"]),(-2,C["red"]),(0,C["border"])]:
                fig_n.add_hline(y=lvl,line_color=col,line_dash="dot" if abs(lvl)==2 else "dash",line_width=1,row=1,col=1)
            fig_n.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_MinMax"],
                line=dict(color=C["teal"],width=1.5),fill="tozeroy",fillcolor=f"rgba(0,204,205,.07)"),row=2,col=1)
            fig_n.update_layout(**PLT,height=380,showlegend=False,margin=dict(l=0,r=0,t=28,b=0))
            fig_n.update_xaxes(gridcolor=C["border"]); fig_n.update_yaxes(gridcolor=C["border"])
            st.plotly_chart(fig_n,use_container_width=True)

        elif "Cyclic" in sel:
            info("Mon=1…Sun=7 tells a model Sunday is far from Monday. They're adjacent. Sine/cosine place days on a circle so every day is equidistant from its neighbours.")
            fml("sin_dow = sin(2π × day / 7)\ncos_dow = cos(2π × day / 7)")
            dc=feat_df.groupby("day_of_week")[["sin_dow","cos_dow"]].first()
            dl=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            theta=np.linspace(0,2*np.pi,200)
            fig_c=go.Figure()
            fig_c.add_trace(go.Scatter(x=np.sin(theta),y=np.cos(theta),mode="lines",
                line=dict(color=C["border"],width=1.5),showlegend=False))
            dr_=feat_df.groupby("day_of_week")["Revenue_USD"].mean()
            for i,(dow,row) in enumerate(dc.iterrows()):
                fig_c.add_trace(go.Scatter(x=[row["sin_dow"]],y=[row["cos_dow"]],
                    mode="markers+text",marker=dict(size=20,color=COLORS[i],line=dict(color="white",width=2)),
                    text=[f"<b>{dl[dow]}</b>"],textposition="top center",
                    textfont=dict(color=COLORS[i],size=11),
                    name=f"{dl[dow]} (${dr_.get(dow,0):.0f}/day)"))
            fig_c.update_layout(**PLT,height=420,
                xaxis=dict(range=[-1.6,1.6],gridcolor=C["border"]),
                yaxis=dict(range=[-1.6,1.6],gridcolor=C["border"]),
                margin=dict(l=0,r=0,t=40,b=0),legend=dict(font=dict(size=10),x=1.02,y=1))
            st.plotly_chart(fig_c,use_container_width=True)

        elif "Lag" in sel:
            info("A model sees one row at a time — no memory. Lag features copy past revenue into the current row so the model can 'look back'.")
            warn("⚠️ <b>Data leakage:</b> forecasting 7 days ahead means Lag 1–6 don't exist yet at inference time. Minimum safe lag = 7.")
            fml("Y_t = f(Y_{t-1}, Y_{t-7}, ...) + ε")
            lm=st.slider("Lags to show",3,14,14)
            lc=[f"lag_{i}" for i in range(1,lm+1)]
            cv=[feat_df["Revenue_USD"].corr(feat_df[c]) for c in lc]
            best=max(range(len(cv)),key=lambda i:abs(cv[i]))
            fig_l=go.Figure(go.Bar(x=[f"Lag {i}" for i in range(1,lm+1)],y=cv,
                marker_color=[C["green"] if i==best else (C["purple"] if v>=0 else C["red"]) for i,v in enumerate(cv)],
                text=[f"{v:.3f}" for v in cv],textposition="outside"))
            fig_l.add_hline(y=0,line_color=C["border"],line_width=1)
            fig_l.update_layout(**PLT,height=300,
                title=f"Lag {best+1} is the strongest predictor (r={cv[best]:.3f})",
                yaxis=dict(gridcolor=C["border"]),xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_l,use_container_width=True)

        elif "Stationarity" in sel:
            info("ARIMA needs constant mean and variance. If revenue is trending up, we subtract yesterday from today — predicting change instead of level.")
            fml("ΔY_t = Y_t − Y_{t-1}    ← predict change, not level")
            if adf_df is not None:
                c1_,c2_,c3_ = st.columns(3)
                for col,(i,row) in zip([c1_,c2_,c3_],enumerate(adf_df.itertuples())):
                    ok="YES" in str(row.Stationary)
                    col.metric(row.Series,f"p={row.p_value:.4f}",
                        delta="✅ Stationary" if ok else "⚠️ Not stationary",
                        delta_color="normal" if ok else "inverse")
            fig_d=make_subplots(rows=2,cols=1,subplot_titles=("Raw revenue","After differencing — bounded around 0"),vertical_spacing=0.14)
            fig_d.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_USD"],
                line=dict(color=C["purple"],width=1.5),fill="tozeroy",fillcolor=f"rgba(67,58,142,.07)"),row=1,col=1)
            fig_d.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["revenue_diff1"],
                line=dict(color=C["teal"],width=1.5),fill="tozeroy",fillcolor=f"rgba(0,204,205,.07)"),row=2,col=1)
            fig_d.add_hline(y=0,line_color=C["border"],line_dash="dash",row=2,col=1)
            fig_d.update_layout(**PLT,height=380,showlegend=False,margin=dict(l=0,r=0,t=28,b=0))
            fig_d.update_xaxes(gridcolor=C["border"]); fig_d.update_yaxes(gridcolor=C["border"])
            st.plotly_chart(fig_d,use_container_width=True)

        elif "VIF" in sel:
            info("VIF detects when two features say the same thing. High VIF (>10) = model can't decide which to trust. Drop or combine with PCA.")
            fml("VIF = 1/(1−R²)  ·  >10 = redundant, consider dropping")
            if vif_df is not None:
                fig_v=go.Figure(go.Bar(x=vif_df["VIF"],y=vif_df["Feature"],orientation="h",
                    marker_color=["#ef4444" if v>10 else (C["amber"] if v>5 else C["green"]) for v in vif_df["VIF"]],
                    text=[f"{v:.1f}" for v in vif_df["VIF"]],textposition="outside"))
                fig_v.add_vline(x=5, line_color=C["amber"],line_dash="dot",line_width=1.5)
                fig_v.add_vline(x=10,line_color=C["red"],  line_dash="dot",line_width=1.5)
                fig_v.update_layout(**PLT,height=380,
                    title="green=keep · yellow=watch · red=drop",
                    xaxis=dict(gridcolor=C["border"]),yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0,r=60,t=40,b=0))
                st.plotly_chart(fig_v,use_container_width=True)

    elif st.session_state.page == "upload":
        st.markdown('<div class="pg-title">📤 Upload Your Data</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Replace the sample data with your own sales and inventory CSVs.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Sales / Transactions CSV**")
            f = st.file_uploader("", type=["csv"], key="txn_upload")
            if f:
                df = pd.read_csv(f, parse_dates=["Transaction_Date"])
                os.makedirs("data/raw", exist_ok=True)
                df.to_csv("data/raw/transactions.csv", index=False)
                st.cache_data.clear()
                st.success(f"Saved {len(df):,} rows to data/raw/transactions.csv")
        with col2:
            st.markdown("**Inventory CSV**")
            f2 = st.file_uploader("", type=["csv"], key="inv_upload")
            if f2:
                df2 = pd.read_csv(f2)
                os.makedirs("data/raw", exist_ok=True)
                df2.to_csv("data/raw/inventory.csv", index=False)
                st.cache_data.clear()
                st.success(f"Saved {len(df2):,} rows to data/raw/inventory.csv")
        with st.expander("Required column names"):
            st.code("Transactions: Transaction_Date, Transaction_ID, Customer_ID,\nProduct_ID, Product_Name, Quantity, Line_Total_USD, Category")
            st.code("Inventory: Product_ID, Product_Name, Category,\nCurrent_Stock, Retail_Price, Cost_Price")

    elif st.session_state.page == "profit":
        st.markdown('<div class="pg-title">💰 Profit Margin Optimizer</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Gross margin per product · dead stock cost · price simulator</div>', unsafe_allow_html=True)
        if not guard(prod_df,"product metrics"): st.stop()

        margin_sorted = prod_df.sort_values("Gross_Margin_Pct", ascending=False)
        fig_m = go.Figure(go.Bar(
            x=margin_sorted["Gross_Margin_Pct"], y=margin_sorted["Product_Name"],
            orientation="h",
            marker_color=[C["green"] if v>=40 else (C["amber"] if v>=20 else C["red"]) for v in margin_sorted["Gross_Margin_Pct"]],
            text=[f"{v:.1f}%" for v in margin_sorted["Gross_Margin_Pct"]],
            textposition="outside"))
        fig_m.add_vline(x=40, line_color=C["green"], line_dash="dot", line_width=1.5, annotation_text="40%", annotation_font_color=C["muted"], annotation_font_size=10)
        fig_m.add_vline(x=20, line_color=C["amber"], line_dash="dot", line_width=1.5, annotation_text="20%", annotation_font_color=C["muted"], annotation_font_size=10)
        fig_m.update_layout(**PLT, height=500, margin=dict(l=0,r=60,t=10,b=0),
            xaxis=dict(title="Gross Margin %", gridcolor=C["border"]),
            yaxis=dict(tickfont=dict(size=10), gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_m, use_container_width=True)

        st.markdown(f'<hr style="border-color:{C["border"]};margin:24px 0">', unsafe_allow_html=True)
        sec("Dead Stock Cost Calculator")
        dead = prod_df[prod_df["Sell_Through_Pct"] < 10].copy() if "Sell_Through_Pct" in prod_df.columns else pd.DataFrame()
        if dead is not None and len(dead) > 0:
            dead["Capital_Tied_Up"] = (dead["Current_Stock"] * dead["Cost_Price"]).round(2)
            show = dead[["Product_Name","Current_Stock","Cost_Price","Capital_Tied_Up","Sell_Through_Pct"]].sort_values("Capital_Tied_Up", ascending=False)
            st.dataframe(show, use_container_width=True)
            warn(f"Total capital tied up in dead stock: <b>${show['Capital_Tied_Up'].sum():,.2f}</b>")
        else:
            good("No dead stock detected (sell-through > 10% on all products).")

    elif st.session_state.page == "glossary":
        st.markdown('<div class="pg-title">📖 Glossary</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Plain-English definitions for every metric and concept. No prior knowledge required.</div>', unsafe_allow_html=True)

    elif st.session_state.page == "onboarding":
        st.markdown('<div class="pg-title">🚀 First-Time Setup</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Get Navigare tailored to your store in 4 steps.</div>', unsafe_allow_html=True)

        step = st.session_state.get("onboard_step", 1)

        if step == 1:
            st.markdown("**Step 1 — What kind of store are you?**")
            stype = st.selectbox("Store Type", ["Retail", "Food/Bakery", "Service", "E-Commerce"])
            sname = st.text_input("Store Name")
            if st.button("Next →"):
                st.session_state.store_type = stype
                st.session_state.store_name = sname
                st.session_state.onboard_step = 2
                st.rerun()

        elif step == 2:
            st.markdown("**Step 2 — Upload your sales data**")
            st.info("Download our sample CSV, fill it with your data, then upload it here.")
            f = st.file_uploader("Transactions CSV", type=["csv"])
            if f:
                df = pd.read_csv(f, parse_dates=["Transaction_Date"])
                df.to_csv("data/raw/transactions.csv", index=False)
                st.cache_data.clear()
                st.success(f"Saved {len(df):,} rows")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back"): st.session_state.onboard_step = 1; st.rerun()
            with c2:
                if st.button("Next →"): st.session_state.onboard_step = 3; st.rerun()

        elif step == 3:
            st.markdown("**Step 3 — Set restock thresholds**")
            threshold = st.slider("Alert me when stock falls below", 5, 50, 10)
            st.session_state.reorder_threshold = threshold
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back"): st.session_state.onboard_step = 2; st.rerun()
            with c2:
                if st.button("Next →"): st.session_state.onboard_step = 4; st.rerun()

        elif step == 4:
            st.markdown("**Step 4 — Set up weekly digest**")
            email = st.text_input("Digest Email")
            day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            time = st.time_input("Time")
            st.session_state.digest_email = email
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back"): st.session_state.onboard_step = 3; st.rerun()
            with c2:
                if st.button("Finish Setup", type="primary"):
                    st.session_state.onboarded = True
                    st.session_state.page = "overview"
                    st.rerun()
        st.markdown('<div class="pg-title">📖 Glossary</div>', unsafe_allow_html=True)
        st.markdown('<div class="pg-sub">Plain-English definitions for every metric and concept. No prior knowledge required.</div>', unsafe_allow_html=True)

    G = [
        ("H(x) — Inventory Health Score","Asymmetric function per SKU. Score 0–100. Steep penalty near zero (stockout = sale loss + customer decay). Gentle penalty for overstock (holding cost).","H(x): 0→CRISIS·1-5→CRITICAL·6-10→LOW·11-20→WARNING·21-50→HEALTHY·51-100→OPTIMAL·>100→OVERSTOCK"),
        ("μ — Store Wellness Index","Mean of all SKU health scores. The single number summarising the whole store's stock position.","μ = (1/N) × Σ H(xᵢ)"),
        ("M — Boolean Mask","M=1 if status ∈ {CRISIS,CRITICAL,LOW}. Backend computes M; UI renders M=1 rows only (Layout Presentation Separation).","M_i = 1 if status=='CRISIS', else 0"),
        ("MAD — Mean Absolute Deviation","How much daily demand fluctuates. High MAD = unpredictable = needs more safety stock.","MAD = avg |daily_demand − avg_demand|"),
        ("Safety Stock","Buffer inventory for demand spikes during supplier lead time.","Safety Stock = Z × MAD × √(Lead Time) · Z=1.65→95%"),
        ("ROP — Reorder Point","Stock level that triggers a new order.","ROP = (Avg Daily Demand × Lead Time) + Safety Stock"),
        ("Gross Margin %","% of each sale that is profit after subtracting cost of goods.","Gross Margin = (Retail − Cost) / Retail × 100"),
        ("Sell-Through %","What fraction of available stock was sold.","Sell-Through = Units Sold / (Units Sold + Stock) × 100"),
        ("EMA — Exponential Moving Average","Moving average weighting recent days more. Reacts faster than SMA.","EMA_t = α×today + (1−α)×EMA_{t-1} · α=2/(N+1)"),
        ("SMA — Simple Moving Average","Averages the last N days equally. Simple but lags behind sudden changes.","SMA = sum of last N days / N"),
        ("Holt-Winters","Forecasting tracking level + trend + seasonality.","3 components: Level α · Trend β · Seasonality γ"),
        ("RFM","Customer scoring: Recency + Frequency + Monetary. Score 3–9.","Champion(8-9)·Loyal(6-7)·Potential(4-5)·At Risk(3)"),
        ("Lift","How much more likely B is bought when A is in the cart vs random.","Lift = Confidence(A→B) / Support(B) · >1=genuine pair"),
        ("Support","% of all orders containing a specific product or pair.","Support = orders_with_pair / total_orders"),
        ("Confidence","If customer buys A, probability they buy B.","Confidence(A→B) = Support(A,B) / Support(A)"),
        ("Keyword Density","% of total words that is a specific keyword.","Density = (matches / total_tokens) × 100"),
        ("SEO Sweet Spot","1–3.5% density. Human-authored content, crawler trusts it.","Score = 100 when 1% ≤ density ≤ 3.5%"),
        ("Keyword Stuffing","Density >3.5%. Score = max(0, 100−(excess×15)).","excess = density−3.5% · penalty = excess×15"),
        ("Sliding Window N-Gram","Scans tokens for multi-word phrases by sliding a window of width N.","for i in range(len(tokens)−N+1): check tokens[i:i+N]"),
        ("Z-Score","Standard deviations from mean. 0=average, ±2=outlier.","Z = (x − μ) / σ"),
        ("Min-Max Scaling","Squeezes all values to 0–1.","X' = (x − min) / (max − min)"),
        ("Cyclic Time Encoding","Projects days onto a circle — Sun stays adjacent to Mon.","sin=sin(2π×day/7) · cos=cos(2π×day/7)"),
        ("Lag Features","Past values copied forward so model can see history.","lag_1=yesterday · lag_7=last week"),
        ("First-Order Differencing","Predict daily change, not level. Removes trends.","ΔY_t = Y_t − Y_{t-1}"),
        ("VIF — Variance Inflation Factor","Detects redundant features. VIF>10 → drop.","VIF = 1/(1−R²)"),
        ("@st.cache_data","RAM caching. Disk I/O exactly once. Subsequent calls served from RAM.","Hit <0.1s · Miss ~250ms · Flush: st.cache_data.clear()"),
        ("Defensive Guard Wall","N=0 → safe UI + halt math. N>0 → run formulas.","if len(df)==0: st.info() + st.stop()"),
        ("Layout Presentation Separation","Backend computes data; frontend only renders. Math and display are decoupled.","Backend: M=mask · Frontend: render df[df.M==1]"),
        ("Service Level","Target in-stock probability. Z=1.65→95%, Z=2.05→98%.","Higher service level = more safety stock = higher cost"),
        ("Lead Time","Days between placing order and receiving stock. Default=7 days.","Used in: ROP = (Avg Demand × Lead Time) + Safety Stock"),
    ]

    search = st.text_input("","",placeholder="🔍  Search any term…")
    filtered = [(t,p,f) for t,p,f in G if search.lower() in t.lower() or search.lower() in p.lower()]
    st.markdown(f"<div style='font-size:11px;color:{C['muted']};margin-bottom:14px'>{len(filtered)} terms</div>", unsafe_allow_html=True)
    for term,plain,form in filtered:
        st.markdown(f"""
        <div class="gcard">
          <div class="gcard-term">{term}</div>
          <div class="gcard-plain">{plain}</div>
          <div class="gcard-formula">{form}</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='margin-top:48px;padding-top:14px;border-top:1px solid {C["border"]};
    color:{C["muted"]};font-size:10.5px;text-align:center'>
  🧭 Navigare · Retail Analytics · Week 9 · Phase 4 ·
  <a href="https://github.com/SS10-code/Navigare" style="color:{C['purple']}">github.com/SS10-code/Navigare</a>
</div>""", unsafe_allow_html=True)