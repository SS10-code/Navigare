"""
dashboard.py — Navigare Retail Analytics  v4
Week 7 · SEO Auditor + Business Metrics + Forecasting + Glossary

Sidebar pages:
  Overview · Inventory Health · What Sells Together
  Customer Segments · Sales Forecast · SEO Auditor
  Under the Hood · Glossary

Run:  streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings, os, json, random
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

# ── import our SEO engine (same folder) ───────────────────────
import sys
sys.path.insert(0, os.path.dirname(__file__))
from seo_engine import analyse_text, score_density, normalize, STOP_WORDS

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG & STYLES
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Navigare · Retail Analytics",
                   page_icon="🧭", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]  { background:#08101f; }
[data-testid="stSidebar"]           { background:#060d1a; border-right:1px solid #0d1e38; }
.main .block-container              { padding:2rem 2.5rem 4rem; max-width:1300px; }

div[data-testid="stSidebar"] .stButton>button {
    width:100%;text-align:left;background:transparent;border:none;
    border-radius:8px;color:#4a6fa5;padding:9px 13px;
    font-size:13px;font-weight:500;transition:all .12s;margin-bottom:2px;
}
div[data-testid="stSidebar"] .stButton>button:hover{background:#0c1e38;color:#c5d8f0;}

.kpi-row{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;}
.kpi{flex:1;min-width:120px;background:linear-gradient(135deg,#0b1828,#101e38);
    border:1px solid #0d2240;border-radius:11px;padding:15px 16px;}
.kpi-label{color:#3a5f8a;font-size:10px;font-weight:700;text-transform:uppercase;
    letter-spacing:1px;margin-bottom:4px;}
.kpi-value{color:#e0ecff;font-size:22px;font-weight:800;line-height:1.1;}
.kpi-sub  {color:#1e3a5a;font-size:10.5px;margin-top:2px;}

.pg-title{font-size:20px;font-weight:800;color:#e0ecff;margin-bottom:3px;}
.pg-sub  {font-size:13px;color:#3a5f8a;margin-bottom:20px;line-height:1.55;}

.explain{background:#080f22;border-left:3px solid #1a45a8;border-radius:0 8px 8px 0;
    padding:12px 16px;margin:0 0 16px;color:#afc8e8;font-size:13px;line-height:1.7;}
.explain b{color:#6aa0f5;}
.explain code{background:#0c1c38;padding:1px 5px;border-radius:4px;
    font-size:11.5px;color:#7ee8a2;}
.warn{background:#180e00;border-left:3px solid #c97a06;border-radius:0 8px 8px 0;
    padding:10px 14px;margin:0 0 14px;color:#f5be5a;font-size:12.5px;}
.good{background:#071408;border-left:3px solid #16a34a;border-radius:0 8px 8px 0;
    padding:10px 14px;margin:0 0 14px;color:#6ee7a0;font-size:12.5px;}
.formula{background:#040c04;border:1px solid #1a3a1a;border-radius:8px;
    padding:12px 16px;font-family:monospace;font-size:12.5px;
    color:#6ee7b7;margin:10px 0;line-height:2;}
.sec{font-size:10px;font-weight:700;color:#1a45a8;text-transform:uppercase;
    letter-spacing:1.2px;margin:24px 0 8px;}
.divider{border:none;border-top:1px solid #0d1e38;margin:20px 0;}

/* SEO score meter colors */
.score-critical { color:#ef4444; font-weight:800; font-size:28px; }
.score-high     { color:#f97316; font-weight:800; font-size:28px; }
.score-medium   { color:#eab308; font-weight:800; font-size:28px; }
.score-good     { color:#22c55e; font-weight:800; font-size:28px; }

/* Glossary */
.gcard{background:#080f22;border:1px solid #0d2240;border-radius:9px;
    padding:12px 16px;margin-bottom:10px;}
.gcard-term{font-size:13.5px;font-weight:700;color:#6aa0f5;margin-bottom:5px;}
.gcard-plain{font-size:12.5px;color:#afc8e8;margin-bottom:7px;line-height:1.6;}
.gcard-formula{font-family:monospace;font-size:11.5px;color:#6ee7b7;
    background:#040c04;border-radius:4px;padding:5px 9px;display:inline-block;}
</style>
""", unsafe_allow_html=True)

B=dict(template="plotly_dark",paper_bgcolor="#08101f",plot_bgcolor="#090f22")
BL="#3b6fd4";BY="#f59e0b";BG="#22c55e";BP="#a855f7";BR="#ef4444";BC="#06b6d4"
SEV_COLOR={"none":BG,"low":"#86efac","medium":BY,"high":"#f97316","critical":BR}


# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load():
    TODAY=datetime.today().date()
    rng=np.random.default_rng(42);random.seed(42)
    def rd(p,**k): return pd.read_csv(p,**k) if os.path.exists(p) else None

    txn=rd("data/clean/unified_transactions.csv",parse_dates=["Transaction_Date"])
    if txn is None: txn=rd("data/raw/transactions.csv",parse_dates=["Transaction_Date"])
    if txn is None:
        cats=["Pastries","Breads","Cakes","Drinks","Savory"]
        types=["E-Commerce","Brick-and-Mortar"]
        base=datetime.combine(TODAY-timedelta(days=365),datetime.min.time())
        rows=[]
        for i in range(1200):
            st_=random.choice(types);ts=base+timedelta(days=int(rng.integers(0,364)),hours=int(rng.integers(8,20)),minutes=int(rng.integers(0,59)))
            p=round(float(rng.uniform(2.5,35)),2);q=int(rng.integers(1,6))
            rows.append({"Store_Type":st_,"Transaction_ID":f"TXN-{i:05d}","Customer_ID":f"C{rng.integers(1,61):04d}","Product_ID":int(rng.integers(1,26)),"Item_Price_USD":p,"Quantity":q,"Line_Total_USD":round(p*q,2),"Transaction_Date":ts.date(),"Category":random.choice(cats),"Source_Currency":"BRL" if st_=="E-Commerce" else "GBP"})
        txn=pd.DataFrame(rows);txn["Transaction_Date"]=pd.to_datetime(txn["Transaction_Date"])
    if "Store_Type" not in txn.columns or txn["Store_Type"].isna().all():
        txn["Store_Type"]=txn.get("Source_Currency",pd.Series()).map({"BRL":"E-Commerce","GBP":"Brick-and-Mortar"}).fillna("E-Commerce")
    if "Line_Total_USD" not in txn.columns and "Line_Total" in txn.columns: txn["Line_Total_USD"]=txn["Line_Total"]
    if "Line_Total" not in txn.columns and "Line_Total_USD" in txn.columns: txn["Line_Total"]=txn["Line_Total_USD"]

    daily=(txn.groupby("Transaction_Date")["Line_Total_USD"].sum().resample("D").sum().fillna(0).reset_index())
    daily.columns=["Date","Revenue_USD"];daily=daily.sort_values("Date").reset_index(drop=True)

    return (txn,daily,rd("data/clean/inventory_metrics.csv"),rd("data/clean/product_metrics.csv"),
            rd("data/clean/customer_rfm.csv"),rd("data/clean/combo_pairs.csv"),
            rd("data/clean/features.csv",parse_dates=["Date"]),
            rd("data/clean/ema_forecast.csv",parse_dates=["Date"]),
            rd("data/clean/adf_results.csv"),rd("data/clean/vif_results.csv"),
            json.load(open("data/clean/chaos_report.json")) if os.path.exists("data/clean/chaos_report.json") else None)

with st.spinner("Loading…"):
    txn_df,daily_df,inv_df,prod_df,rfm_df,combo_df,feat_df,ema_df,adf_df,vif_df,chaos=load()


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding:12px 0 16px'><div style='font-size:18px;font-weight:800;color:#e0ecff'>🧭 Navigare</div><div style='font-size:10px;color:#1e3a5a;margin-top:2px'>Retail Analytics · Phase 3</div></div>",unsafe_allow_html=True)

    PAGES={"📊  Overview":"overview","📦  Inventory Health":"inventory",
           "🛒  What Sells Together":"combo","👥  Customer Segments":"customers",
           "📈  Sales Forecast":"forecast","🔍  SEO Auditor":"seo",
           "🔬  Under the Hood":"features","📖  Glossary":"glossary"}

    if "page" not in st.session_state: st.session_state.page="overview"
    for label,key in PAGES.items():
        if st.button(label,key=f"nav_{key}",use_container_width=True):
            st.session_state.page=key;st.rerun()

    st.markdown("<hr style='border-color:#0d1e38;margin:14px 0'>",unsafe_allow_html=True)
    store_opts=["All Stores"]+sorted(txn_df["Store_Type"].dropna().unique().tolist())
    sel_store=st.selectbox("Store",store_opts,label_visibility="collapsed")
    d_min=txn_df["Transaction_Date"].min().date();d_max=txn_df["Transaction_Date"].max().date()
    dr=st.date_input("Dates",(d_min,d_max),min_value=d_min,max_value=d_max,label_visibility="collapsed")
    st.markdown("<hr style='border-color:#0d1e38;margin:14px 0'>",unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:9.5px;color:#1e3a5a'>Total Revenue</div><div style='font-size:16px;font-weight:800;color:#22c55e'>${txn_df['Line_Total_USD'].sum():,.0f}</div><div style='font-size:9.5px;color:#1e3a5a;margin-top:5px'>{d_min} → {d_max}</div>",unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#0d1e38;margin:14px 0'>",unsafe_allow_html=True)
    if st.button("↻  Refresh",use_container_width=True): st.cache_data.clear();st.rerun()

filt=txn_df.copy()
if sel_store!="All Stores": filt=filt[filt["Store_Type"]==sel_store]
if len(dr)==2: filt=filt[(filt["Transaction_Date"].dt.date>=dr[0])&(filt["Transaction_Date"].dt.date<=dr[1])]
ds=(filt.groupby("Transaction_Date")["Line_Total_USD"].sum().resample("D").sum().fillna(0))

def kpis(m):
    html='<div class="kpi-row">'
    for l,v,s in m: html+=f'<div class="kpi"><div class="kpi-label">{l}</div><div class="kpi-value">{v}</div><div class="kpi-sub">{s}</div></div>'
    html+='</div>';st.markdown(html,unsafe_allow_html=True)
def sec(t): st.markdown(f'<div class="sec">{t}</div>',unsafe_allow_html=True)
def expl(t): st.markdown(f'<div class="explain">{t}</div>',unsafe_allow_html=True)
def warn(t): st.markdown(f'<div class="warn">{t}</div>',unsafe_allow_html=True)
def good(t): st.markdown(f'<div class="good">{t}</div>',unsafe_allow_html=True)
def fml(t):  st.markdown(f'<div class="formula">{t}</div>',unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# OVERVIEW
# ═════════════════════════════════════════════════════════════
if st.session_state.page=="overview":
    st.markdown('<div class="pg-title">📊 Store Overview</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Everything at a glance. Use the sidebar filters to narrow by store type or date range.</div>',unsafe_allow_html=True)
    rev=filt["Line_Total_USD"].sum();orders=filt["Transaction_ID"].nunique()
    aov=filt.groupby("Transaction_ID")["Line_Total_USD"].sum().mean() if orders>0 else 0
    low=int(inv_df["Order_Now"].sum()) if inv_df is not None and "Order_Now" in inv_df.columns else 0
    kpis([("Revenue",f"${rev:,.0f}",sel_store),("Orders",f"{orders:,}","transactions"),
          ("Avg Order",f"${aov:,.2f}","per checkout"),("Reorder Alerts",f"{low}","order now")])
    c1,c2=st.columns([3,1])
    with c1:
        sec("Daily Revenue")
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=ds.index,y=ds.values,fill="tozeroy",fillcolor="rgba(59,111,212,0.09)",line=dict(color=BL,width=2),name="Daily"))
        roll=ds.rolling(7,min_periods=1).mean()
        fig.add_trace(go.Scatter(x=roll.index,y=roll.values,line=dict(color=BY,width=2,dash="dash"),name="7-day avg"))
        fig.update_layout(**B,height=300,hovermode="x unified",margin=dict(l=0,r=0,t=8,b=0),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        sec("By Channel")
        rv=filt.groupby("Store_Type")["Line_Total_USD"].sum().reset_index()
        fig_pie=px.pie(rv,values="Line_Total_USD",names="Store_Type",color_discrete_sequence=[BL,BY],hole=0.55)
        fig_pie.update_layout(**B,height=250,margin=dict(l=0,r=0,t=0,b=0),showlegend=True,legend=dict(orientation="h",y=-0.15))
        fig_pie.update_traces(textinfo="percent+label",textfont_size=10)
        st.plotly_chart(fig_pie,use_container_width=True)
    if prod_df is not None:
        sec("Top Products by Revenue")
        top=prod_df.nlargest(10,"Total_Revenue")
        fig_b=go.Figure(go.Bar(x=top["Total_Revenue"],y=top["Product_Name"],orientation="h",marker_color=BL,text=[f"${v:,.0f}" for v in top["Total_Revenue"]],textposition="outside"))
        fig_b.update_layout(**B,height=300,margin=dict(l=0,r=0,t=8,b=0))
        st.plotly_chart(fig_b,use_container_width=True)


# ═════════════════════════════════════════════════════════════
# INVENTORY
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="inventory":
    st.markdown('<div class="pg-title">📦 Inventory Health</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Know exactly which products to reorder and when — using demand-based math instead of gut feel.</div>',unsafe_allow_html=True)
    if inv_df is None: st.warning("Run `python business_metrics.py` first");st.stop()
    order_now=inv_df[inv_df["Order_Now"]==1];ok=inv_df[inv_df["Order_Now"]==0]
    kpis([("Total SKUs",f"{len(inv_df)}","products"),("Order Now ⚠️",f"{len(order_now)}","at or below ROP"),
          ("Safe Stock ✅",f"{len(ok)}","healthy"),("Avg Safety Stock",f"{inv_df['Safety_Stock'].mean():.1f} units","95% service level"),
          ("Avg Reorder Point",f"{inv_df['ROP'].mean():.1f} units","7-day lead time")])
    expl("""<b>Three metrics power this page:</b><br><br>
    <b>MAD</b> — how much daily demand fluctuates. High MAD = unpredictable = needs more buffer.<br>
    <b>Safety Stock</b> — buffer to survive demand spikes during supplier lead time.
    Formula: <code>Z × MAD × √(Lead Time)</code> where Z=1.65 targets 95% in-stock rate.<br>
    <b>Reorder Point (ROP)</b> — when stock hits this level, place your order immediately.
    Formula: <code>(Avg Daily Demand × Lead Time) + Safety Stock</code>""")
    sec("Current Stock vs Reorder Point")
    fig_rop=go.Figure()
    fig_rop.add_trace(go.Bar(name="Current Stock",x=inv_df["Product_Name"],y=inv_df["Current_Stock"],marker_color=BL))
    fig_rop.add_trace(go.Scatter(name="Reorder Point",x=inv_df["Product_Name"],y=inv_df["ROP"],mode="markers",marker=dict(symbol="line-ew",size=14,color=BR,line=dict(width=2,color=BR))))
    fig_rop.add_trace(go.Scatter(name="Safety Stock",x=inv_df["Product_Name"],y=inv_df["Safety_Stock"],mode="lines",line=dict(color=BY,width=1.5,dash="dot")))
    fig_rop.update_layout(**B,height=360,hovermode="x",barmode="overlay",margin=dict(l=0,r=0,t=8,b=0),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig_rop.update_xaxes(tickangle=-40,tickfont=dict(size=9))
    st.plotly_chart(fig_rop,use_container_width=True)
    warn("⚠️  Any product where the bar (current stock) falls below the red dash (ROP) needs to be ordered today.")
    sec("Demand Variability (MAD)")
    fig_mad=go.Figure(go.Bar(x=inv_df.sort_values("MAD")["Product_Name"],y=inv_df.sort_values("MAD")["MAD"],marker_color=[BR if v>1.5 else (BY if v>1.0 else BG) for v in inv_df.sort_values("MAD")["MAD"]],text=[f"{v:.2f}" for v in inv_df.sort_values("MAD")["MAD"]],textposition="outside"))
    fig_mad.update_layout(**B,height=300,margin=dict(l=0,r=0,t=8,b=0),yaxis_title="MAD (units/day)")
    fig_mad.update_xaxes(tickangle=-40,tickfont=dict(size=9))
    st.plotly_chart(fig_mad,use_container_width=True)
    sec("Full Reorder Table")
    disp=inv_df[["Product_Name","Category","Current_Stock","Safety_Stock","ROP","Avg_Daily_Demand","MAD","Units_Below_ROP","Order_Now"]].copy()
    disp.columns=["Product","Category","Stock Now","Safety Stock","Reorder Point","Avg Daily Sales","MAD","Units Short","Order Now?"]
    disp["Order Now?"]=disp["Order Now?"].map({1:"🔴 YES",0:"✅ No"})
    st.dataframe(disp,use_container_width=True,height=360)
    if prod_df is not None:
        sec("Margin vs Sell-Through")
        fig_sc=px.scatter(prod_df,x="Sell_Through_Pct",y="Gross_Margin_Pct",size="Total_Revenue",color="Category",hover_name="Product_Name",color_discrete_sequence=px.colors.qualitative.Bold,labels={"Sell_Through_Pct":"Sell-Through %","Gross_Margin_Pct":"Gross Margin %"})
        fig_sc.update_layout(**B,height=360,margin=dict(l=0,r=0,t=8,b=0))
        st.plotly_chart(fig_sc,use_container_width=True)
        expl("""<b>Top-right</b> (high margin + high sell-through) = best products — never let these stock out.<br>
        <b>Top-left</b> (high margin + low sell-through) = profitable but slow — try promotions.<br>
        <b>Bottom-right</b> (low margin + high sell-through) = high volume, low profit — review pricing.<br>
        <b>Bottom-left</b> = consider discontinuing.""")


# ═════════════════════════════════════════════════════════════
# COMBO
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="combo":
    st.markdown('<div class="pg-title">🛒 What Sells Together</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Find product pairs that customers frequently buy in the same order. Use this to design bundles, promotions, and shelf placement.</div>',unsafe_allow_html=True)
    if combo_df is None: st.warning("Run `python business_metrics.py` first");st.stop()
    expl("""<b>Support</b> — % of all orders containing this pair.<br>
    <b>Confidence</b> — if a customer buys A, probability they also buy B.<br>
    <b>Lift</b> — most important number. Lift > 1 means the pair sells together more than random chance.
    Lift = 2.5 means 2.5× more likely than if they were unrelated.<br><br>
    <b>Scalability:</b> with 25 SKUs we check 300 pairs directly. At 500+ SKUs we'd need Apriori or FP-Growth to avoid checking 125,000 pairs.""")
    kpis([("Pairs Found",f"{len(combo_df)}","above min threshold"),("Top Lift",f"{combo_df['Lift'].max():.2f}×","strongest link"),
          ("Avg Confidence",f"{combo_df['Confidence_AB'].mean():.1%}","A → buy B"),("Orders Scanned",f"{filt['Transaction_ID'].nunique():,}","basket patterns")])
    sec("Strongest Pairs (by Lift)")
    top=combo_df.head(15)
    fig_c=go.Figure(go.Bar(x=top["Lift"],y=top["Pair_Label"],orientation="h",marker_color=[BG if v>=2 else (BC if v>=1.5 else BL) for v in top["Lift"]],text=[f"{v:.2f}×" for v in top["Lift"]],textposition="outside"))
    fig_c.add_vline(x=1,line_color="#1e3a5a",line_dash="dash",line_width=1)
    fig_c.update_layout(**B,height=440,margin=dict(l=0,r=0,t=8,b=0),xaxis_title="Lift")
    st.plotly_chart(fig_c,use_container_width=True)
    sec("Full Pair Table")
    disp=combo_df.copy()
    disp["Support"]=disp["Support"].apply(lambda x:f"{x:.1%}")
    disp["Confidence_AB"]=disp["Confidence_AB"].apply(lambda x:f"{x:.1%}")
    disp["Lift"]=disp["Lift"].apply(lambda x:f"{x:.2f}×")
    disp.columns=["Pair","Product A","Product B","Orders Together","Support","Confidence (A→B)","Lift"]
    st.dataframe(disp[["Pair","Orders Together","Support","Confidence (A→B)","Lift"]],use_container_width=True,height=300)


# ═════════════════════════════════════════════════════════════
# CUSTOMERS
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="customers":
    st.markdown('<div class="pg-title">👥 Customer Segments</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">RFM scoring groups customers by how recently, how often, and how much they buy. Target loyalty rewards where they count most.</div>',unsafe_allow_html=True)
    if rfm_df is None: st.warning("Run `python business_metrics.py` first");st.stop()
    expl("""<b>Recency (R)</b> — bought recently? 3=yes, 1=a while ago.<br>
    <b>Frequency (F)</b> — how often? 3=frequent, 1=one-time.<br>
    <b>Monetary (M)</b> — how much do they spend? 3=high, 1=low.<br><br>
    Total score 3–9 → <b>Champion</b> (8–9) · <b>Loyal</b> (6–7) · <b>Potential</b> (4–5) · <b>At Risk</b> (3)""")
    seg_counts=rfm_df["Segment"].value_counts();seg_rev=rfm_df.groupby("Segment")["Monetary"].sum()
    kpis([("Champions",f"{seg_counts.get('Champion',0)}","top buyers"),("Loyal",f"{seg_counts.get('Loyal',0)}","consistent"),
          ("Potential",f"{seg_counts.get('Potential',0)}","growing"),("At Risk",f"{seg_counts.get('At Risk',0)}","need attention"),
          ("Avg Spend",f"${rfm_df['Monetary'].mean():,.2f}","per customer")])
    SCOLS={"Champion":BG,"Loyal":BL,"Potential":BC,"At Risk":BR}
    c1,c2=st.columns(2)
    with c1:
        sec("Customers by Segment")
        fig_s=go.Figure(go.Bar(x=seg_counts.index,y=seg_counts.values,marker_color=[SCOLS.get(s,BL) for s in seg_counts.index],text=seg_counts.values,textposition="outside"))
        fig_s.update_layout(**B,height=280,margin=dict(l=0,r=0,t=8,b=0))
        st.plotly_chart(fig_s,use_container_width=True)
    with c2:
        sec("Revenue by Segment")
        fig_r=go.Figure(go.Bar(x=seg_rev.index,y=seg_rev.values,marker_color=[SCOLS.get(s,BL) for s in seg_rev.index],text=[f"${v:,.0f}" for v in seg_rev.values],textposition="outside"))
        fig_r.update_layout(**B,height=280,margin=dict(l=0,r=0,t=8,b=0),yaxis_title="Total Revenue ($)")
        st.plotly_chart(fig_r,use_container_width=True)
    sec("Recency vs Spend")
    fig_sc=px.scatter(rfm_df,x="Recency_Days",y="Monetary",color="Segment",size="Frequency",hover_data=["Customer_ID","Frequency"],color_discrete_map=SCOLS,labels={"Recency_Days":"Days Since Last Purchase","Monetary":"Total Spend ($)"})
    fig_sc.update_layout(**B,height=360,margin=dict(l=0,r=0,t=8,b=0))
    st.plotly_chart(fig_sc,use_container_width=True)
    sec("Customer Table")
    disp=rfm_df[["Customer_ID","Last_Purchase","Recency_Days","Frequency","Monetary","R_Score","F_Score","M_Score","RFM_Score","Segment"]].copy()
    disp["Monetary"]=disp["Monetary"].apply(lambda x:f"${x:,.2f}")
    st.dataframe(disp,use_container_width=True,height=320)


# ═════════════════════════════════════════════════════════════
# FORECAST
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="forecast":
    st.markdown('<div class="pg-title">📈 Sales Forecast</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Three forecasting methods running side by side. Adjust the controls to compare how each handles your data.</div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    sma_w=c1.slider("Smoothing window (days)",3,30,7)
    ema_w=c2.slider("EMA window (days)",3,30,7)
    sp=c3.number_input("Seasonal period (days)",2,30,7)
    fcd=c4.slider("Days to forecast ahead",7,60,14)
    alpha=2/(ema_w+1)
    e1,e2,e3=st.columns(3)
    with e1: expl(f"<b>Simple Moving Average</b><br>Averages the last {sma_w} days equally. Smooth but slow to react.")
    with e2: expl(f"<b>Weighted Average (EMA)</b><br>Recent days count more. Alpha = {alpha:.3f} — weight given to the most recent day.")
    with e3: expl(f"<b>Holt-Winters</b><br>Tracks trend + seasonality simultaneously. Best when weekends differ reliably from weekdays.")
    sma_s=ds.rolling(sma_w,min_periods=1).mean();ema_s=ds.ewm(span=ema_w,adjust=False).mean()
    hw_ok=False
    try:
        hw=ExponentialSmoothing(ds,trend="add",seasonal="add",seasonal_periods=int(sp),initialization_method="estimated").fit(optimized=True)
        hw_fit=hw.fittedvalues;fc_idx=pd.date_range(ds.index[-1]+pd.Timedelta(days=1),periods=fcd,freq="D")
        hw_fc=pd.Series(hw.forecast(fcd).values,index=fc_idx);hw_ok=True
    except Exception as e:
        warn(f"Holt-Winters couldn't fit: {str(e)[:100]}")
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ds.index,y=ds.values,name="Actual",line=dict(color="#2a3f5a",width=1),opacity=0.7))
    fig.add_trace(go.Scatter(x=sma_s.index,y=sma_s.values,name=f"Simple avg ({sma_w}d)",line=dict(color=BY,width=2,dash="dash")))
    fig.add_trace(go.Scatter(x=ema_s.index,y=ema_s.values,name=f"Weighted avg EMA ({ema_w}d)",line=dict(color=BC,width=2.5)))
    if hw_ok:
        fig.add_trace(go.Scatter(x=hw_fit.index,y=hw_fit.values,name="Holt-Winters fitted",line=dict(color=BG,width=2),opacity=0.85))
        fig.add_trace(go.Scatter(x=hw_fc.index,y=hw_fc.values,name=f"Forecast +{fcd}d",line=dict(color=BP,width=2.5,dash="dot"),fill="tozeroy",fillcolor="rgba(168,85,247,0.05)"))
        fig.add_vline(x=ds.index[-1],line_color=BY,line_dash="dash",line_width=1,annotation_text="  Today",annotation_font_color=BY,annotation_font_size=10)
    fig.update_layout(**B,height=400,hovermode="x unified",margin=dict(l=0,r=0,t=10,b=0),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    st.plotly_chart(fig,use_container_width=True)
    if ema_df is not None:
        sec("14-Day Weighted Average Forecast")
        tc1,tc2=st.columns([2,1])
        with tc1:
            fig_e=go.Figure()
            fig_e.add_trace(go.Scatter(x=ds.index[-30:],y=ds.values[-30:],name="Last 30 days",line=dict(color=BL,width=2)))
            fig_e.add_trace(go.Scatter(x=ema_df["Date"],y=ema_df["EMA_Forecast"],name="Forecast",line=dict(color=BC,width=2.5,dash="dot"),fill="tozeroy",fillcolor="rgba(6,182,212,0.06)"))
            fig_e.update_layout(**B,height=240,hovermode="x unified",margin=dict(l=0,r=0,t=8,b=0))
            st.plotly_chart(fig_e,use_container_width=True)
        with tc2:
            d=ema_df[["Date","Day_Ahead","EMA_Forecast"]].copy()
            d["Date"]=pd.to_datetime(d["Date"]).dt.strftime("%b %d")
            d["EMA_Forecast"]=d["EMA_Forecast"].apply(lambda x:f"${x:,.2f}")
            d.columns=["Date","Day","Forecast"];st.dataframe(d,use_container_width=True,height=240)
    if hw_ok:
        sec("Accuracy Comparison")
        act=ds.reindex(hw_fit.index).fillna(0);hw_mae=(act-hw_fit).abs().mean()
        sma_al=sma_s.reindex(ds.index).ffill();sma_mae=(ds-sma_al).abs().mean()
        ema_al=ema_s.reindex(ds.index);ema_mae=(ds-ema_al).abs().mean()
        ac1,ac2,ac3=st.columns(3)
        winner=min([("Simple avg",sma_mae),("Weighted avg",ema_mae),("Holt-Winters",hw_mae)],key=lambda x:x[1])
        for col,name,mae in [(ac1,"Simple avg",sma_mae),(ac2,"Weighted avg",ema_mae),(ac3,"Holt-Winters",hw_mae)]:
            badge=" 🏆" if name==winner[0] else ""
            col.metric(f"{name}{badge}",f"${mae:.2f}/day avg error",delta="most accurate" if name==winner[0] else None,delta_color="normal" if name==winner[0] else "off")


# ═════════════════════════════════════════════════════════════
# SEO AUDITOR  ← NEW
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="seo":
    st.markdown('<div class="pg-title">🔍 SEO Auditor</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Paste in any web copy — your homepage, product description, or Google Business listing — and check how well it\'s optimised for your target keywords. No live scraping, no API keys needed.</div>',unsafe_allow_html=True)

    expl("""<b>How it works:</b><br>
    1. Your text is cleaned and tokenised (lowercase, punctuation stripped, split into words)<br>
    2. A sliding window scans for every keyword phrase — even multi-word ones like "san jose bakery"<br>
    3. Each keyword gets a density score: how often it appears relative to total word count<br>
    4. The density is run through a scoring formula that rewards the sweet spot (1–3.5%) and penalises stuffing<br><br>
    <b>No Google account, no scraping, no API limits.</b> The keyword dictionary lives locally.""")

    # ── Input area ────────────────────────────────────────────
    col_text, col_kw = st.columns([2, 1])

    with col_text:
        sec("Your Web Copy")
        body_text = st.text_area(
            "Paste your web copy here",
            height=260,
            placeholder="Paste your homepage text, product description, blog post, or Google Business listing here…",
            label_visibility="collapsed"
        )
        st.caption(f"Word count: {len(body_text.split()) if body_text.strip() else 0}")

    with col_kw:
        sec("Target Keywords")
        st.markdown('<div class="explain">One keyword or phrase per line.<br>Multi-word phrases like <code>fresh sourdough bread</code> are supported — the sliding window finds exact matches.</div>', unsafe_allow_html=True)

        default_kws = (
            "bakery near me\n"
            "fresh bread\n"
            "custom birthday cake\n"
            "artisan bakery\n"
            "sourdough loaf\n"
            "best bakery\n"
            "coffee and pastries"
        )
        kw_text = st.text_area(
            "Keywords",
            value=default_kws,
            height=200,
            label_visibility="collapsed"
        )
        remove_sw = st.checkbox("Remove stop-words from token count",
                                value=False,
                                help="If checked, common words (the, and, is…) are excluded from the denominator. Results in higher densities.")

    run_audit = st.button("▶  Run SEO Audit", type="primary", use_container_width=False)

    if run_audit:
        if not body_text.strip():
            st.error("Please paste some web copy into the left box first.")
        else:
            keywords = [k.strip() for k in kw_text.strip().splitlines() if k.strip()]
            if not keywords:
                st.error("Please add at least one keyword.")
            else:
                with st.spinner("Analysing…"):
                    report = analyse_text(body_text, keywords, remove_stopwords=remove_sw)

                if "error" in report:
                    st.error(report["error"])
                else:
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

                    # ── Page health score ─────────────────────
                    health = report["page_health_score"]
                    if health >= 90:   hcol, hlabel = BG,  "Excellent"
                    elif health >= 70: hcol, hlabel = BC,  "Good"
                    elif health >= 50: hcol, hlabel = BY,  "Needs Work"
                    else:              hcol, hlabel = BR,  "Poor"

                    h1, h2, h3 = st.columns(3)
                    h1.markdown(f"""
                    <div class="kpi">
                      <div class="kpi-label">Page Health Score</div>
                      <div class="kpi-value" style="color:{hcol};font-size:36px">{health}/100</div>
                      <div class="kpi-sub">{hlabel}</div>
                    </div>""", unsafe_allow_html=True)
                    h2.markdown(f"""
                    <div class="kpi">
                      <div class="kpi-label">Word Count</div>
                      <div class="kpi-value">{report['token_count']}</div>
                      <div class="kpi-sub">tokens after normalisation</div>
                    </div>""", unsafe_allow_html=True)
                    h3.markdown(f"""
                    <div class="kpi">
                      <div class="kpi-label">Keywords Checked</div>
                      <div class="kpi-value">{report['keyword_count']}</div>
                      <div class="kpi-sub">phrases analysed</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

                    # ── Per-keyword results ───────────────────
                    sec("Keyword-by-Keyword Results")

                    results = report["results"]

                    # Score bar chart
                    kw_names  = [r["keyword"]      for r in results if "score" in r]
                    kw_scores = [r["score"]         for r in results if "score" in r]
                    kw_dens   = [r["density_pct"]   for r in results if "score" in r]
                    kw_sevs   = [r["severity"]       for r in results if "score" in r]

                    if kw_names:
                        fig_kw = go.Figure()
                        fig_kw.add_trace(go.Bar(
                            name="Score",
                            x=kw_names, y=kw_scores,
                            marker_color=[SEV_COLOR.get(s, BL) for s in kw_sevs],
                            text=[f"{v}/100" for v in kw_scores],
                            textposition="outside",
                            yaxis="y1"
                        ))
                        fig_kw.add_trace(go.Scatter(
                            name="Density %",
                            x=kw_names, y=kw_dens,
                            mode="lines+markers",
                            line=dict(color=BY, width=2),
                            marker=dict(size=8),
                            yaxis="y2"
                        ))
                        # Sweet-spot band
                        fig_kw.add_hrect(y0=1.0, y1=3.5, fillcolor="rgba(34,197,94,0.06)",
                                         line_width=0, yref="y2",
                                         annotation_text="Sweet spot 1–3.5%",
                                         annotation_font_color=BG, annotation_font_size=10)
                        fig_kw.update_layout(
                            **B, height=360, hovermode="x unified",
                            margin=dict(l=0,r=0,t=10,b=0),
                            yaxis=dict(title="SEO Score (0–100)", range=[0,115]),
                            yaxis2=dict(title="Density %", overlaying="y",
                                        side="right", range=[0, max(kw_dens)*2+1] if kw_dens else [0,10]),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_kw, use_container_width=True)

                    # Detail cards
                    for r in results:
                        if "error" in r:
                            warn(f"'{r['keyword']}' — {r['error']}")
                            continue
                        sev    = r["severity"]
                        scolor = SEV_COLOR.get(sev, BL)
                        score  = r["score"]

                        if sev == "none":
                            box_class = "good"
                        elif sev in ("critical","high"):
                            box_class = "warn"
                        else:
                            box_class = "explain"

                        with st.expander(f"{'✅' if sev=='none' else ('⚠️' if sev in ['medium','low'] else '🔴')}  \"{r['keyword']}\"  —  Score {score}/100  ·  {r['zone']}"):
                            mc1, mc2, mc3, mc4 = st.columns(4)
                            mc1.metric("Score", f"{score}/100")
                            mc2.metric("Matches Found", r["match_count"])
                            mc3.metric("Density", f"{r['density_pct']:.2f}%")
                            mc4.metric("N-Gram Size", f"{r['n_gram_size']} word{'s' if r['n_gram_size']>1 else ''}")

                            st.markdown(f'<div class="{box_class}">{r["explanation"]}</div>',
                                        unsafe_allow_html=True)

                            # Mini gauge
                            fig_g = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=score,
                                gauge=dict(
                                    axis=dict(range=[0,100]),
                                    bar=dict(color=scolor),
                                    steps=[
                                        dict(range=[0,50],  color="#1a0505"),
                                        dict(range=[50,75], color="#1a1005"),
                                        dict(range=[75,100],color="#051a05"),
                                    ],
                                    threshold=dict(line=dict(color=BR,width=2),
                                                   thickness=0.75, value=50)
                                ),
                                number=dict(suffix="/100", font=dict(color=scolor))
                            ))
                            fig_g.update_layout(**B, height=180,
                                                margin=dict(l=20,r=20,t=20,b=0))
                            st.plotly_chart(fig_g, use_container_width=True)

                    # ── Scoring zone explainer ────────────────
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                    sec("How the Scoring Zones Work")
                    fml("""Under-Optimized  (density < 1.0%)      →  Score = 50
  Crawler indexes the page but can't associate it with your keyword

Sweet Spot       (1.0% ≤ density ≤ 3.5%) →  Score = 100
  Content reads as human-authored. Crawler trusts the page.

Over-Stuffed     (density > 3.5%)         →  Score = max(0, int(100 − (excess × 15)))
  Penalty accumulates fast to prevent keyword manipulation""")

                    # Inverted-U curve chart
                    x_range  = np.linspace(0, 12, 300)
                    y_scores = [score_density(float(x))["score"] for x in x_range]
                    fig_zone = go.Figure()
                    fig_zone.add_trace(go.Scatter(x=x_range, y=y_scores,
                        line=dict(color=BL, width=3), name="SEO Score"))
                    fig_zone.add_vrect(x0=0, x1=1.0, fillcolor="rgba(239,68,68,0.08)",
                                       line_width=0, annotation_text="Under-optimized",
                                       annotation_font_color=BR, annotation_font_size=10)
                    fig_zone.add_vrect(x0=1.0, x1=3.5, fillcolor="rgba(34,197,94,0.08)",
                                       line_width=0, annotation_text="Sweet Spot",
                                       annotation_font_color=BG, annotation_font_size=10)
                    fig_zone.add_vrect(x0=3.5, x1=12, fillcolor="rgba(245,158,11,0.06)",
                                       line_width=0, annotation_text="Penalty Zone",
                                       annotation_font_color=BY, annotation_font_size=10)
                    fig_zone.update_layout(**B, height=280,
                        xaxis_title="Keyword Density (%)", yaxis_title="SEO Score",
                        margin=dict(l=0,r=0,t=30,b=0))
                    st.plotly_chart(fig_zone, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# UNDER THE HOOD
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="features":
    st.markdown('<div class="pg-title">🔬 Under the Hood</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">The math behind the forecasting. See the Glossary for plain-English definitions of any term.</div>',unsafe_allow_html=True)
    if feat_df is None: st.warning("Run `python feature_engineering.py` first");st.stop()
    sel=st.selectbox("Jump to",["Normalisation (Z-Score & Min-Max)","Time Encoding (Cyclic)","Memory Features (Lags)","Stationarity & Differencing","Feature Redundancy (VIF)"])
    st.markdown("<hr class='divider'>",unsafe_allow_html=True)

    if "Normalisation" in sel:
        expl("Raw revenue varies wildly. Normalisation puts numbers on the same scale so models don't mistake 'big dollar values' for 'more important'.")
        fml("Z = (x − μ) / σ              ← Z-Score (centres at 0)\nX' = (x − min) / (max − min)  ← Min-Max (squeezes to 0–1)")
        mu=feat_df["Revenue_USD"].mean();sigma=feat_df["Revenue_USD"].std();outs=(feat_df["Revenue_ZScore"].abs()>2).sum()
        m1,m2,m3=st.columns(3);m1.metric("Mean",f"${mu:,.2f}");m2.metric("Std Dev",f"${sigma:,.2f}");m3.metric("Outlier days",f"{outs}")
        fig_n=make_subplots(rows=2,cols=1,subplot_titles=("Z-Score","Min-Max"),vertical_spacing=0.14)
        fig_n.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_ZScore"],line=dict(color=BL,width=1.5),fill="tozeroy",fillcolor="rgba(59,111,212,0.07)"),row=1,col=1)
        for lvl,c in [(2,BR),(-2,BR),(0,"#1a2d4a")]: fig_n.add_hline(y=lvl,line_color=c,line_dash="dot" if abs(lvl)==2 else "dash",line_width=1,row=1,col=1)
        fig_n.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_MinMax"],line=dict(color=BC,width=1.5),fill="tozeroy",fillcolor="rgba(6,182,212,0.07)"),row=2,col=1)
        fig_n.update_layout(**B,height=380,showlegend=False,margin=dict(l=0,r=0,t=28,b=0))
        st.plotly_chart(fig_n,use_container_width=True)

    elif "Cyclic" in sel:
        expl("Mon=1, Sun=7 tells a model they're far apart. They're not. We place days on a circle using sin/cos so every day is equidistant from its neighbours.")
        fml("sin_dow = sin(2π × day / 7)\ncos_dow = cos(2π × day / 7)")
        dow_c=feat_df.groupby("day_of_week")[["sin_dow","cos_dow"]].first()
        dlbls=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];dcols=[BL,"#60a5fa","#93c5fd",BY,"#fcd34d","#f97316",BR]
        theta=np.linspace(0,2*np.pi,200);fig_circ=go.Figure()
        fig_circ.add_trace(go.Scatter(x=np.sin(theta),y=np.cos(theta),mode="lines",line=dict(color="#0f2040",width=1.5),showlegend=False))
        dow_rev=feat_df.groupby("day_of_week")["Revenue_USD"].mean()
        for i,(dow,row) in enumerate(dow_c.iterrows()):
            fig_circ.add_trace(go.Scatter(x=[row["sin_dow"]],y=[row["cos_dow"]],mode="markers+text",marker=dict(size=20,color=dcols[i],line=dict(color="#08101f",width=2)),text=[f"<b>{dlbls[dow]}</b>"],textposition="top center",textfont=dict(color=dcols[i],size=11),name=f"{dlbls[dow]} (${dow_rev.get(dow,0):.0f}/day)"))
        fig_circ.update_layout(**B,height=400,xaxis=dict(range=[-1.6,1.6]),yaxis=dict(range=[-1.6,1.6]),margin=dict(l=0,r=0,t=40,b=0),legend=dict(font=dict(size=10),x=1.02,y=1))
        st.plotly_chart(fig_circ,use_container_width=True)

    elif "Memory" in sel:
        expl("A model sees one row at a time with no memory. Lag features copy past revenue into the current row so the model can 'look back'.")
        warn("⚠️  Deployment leakage: forecasting 7 days ahead means Lag 1–6 don't exist at inference time. Minimum safe lag = 7.")
        fml("Y_t = f(Y_{t-1}, Y_{t-7}, ...) + ε")
        lag_max=st.slider("Lags to display",3,14,14)
        lag_cols=[f"lag_{i}" for i in range(1,lag_max+1)]
        corr_vals=[feat_df["Revenue_USD"].corr(feat_df[c]) for c in lag_cols]
        best=max(range(len(corr_vals)),key=lambda i:abs(corr_vals[i]))
        fig_lag=go.Figure(go.Bar(x=[f"Lag {i}" for i in range(1,lag_max+1)],y=corr_vals,marker_color=[BG if i==best else (BL if v>=0 else BR) for i,v in enumerate(corr_vals)],text=[f"{v:.3f}" for v in corr_vals],textposition="outside"))
        fig_lag.add_hline(y=0,line_color="#1a2d4a",line_width=1)
        fig_lag.update_layout(**B,height=300,title=f"Lag {best+1} is the strongest predictor",yaxis_title="Pearson r",margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_lag,use_container_width=True)

    elif "Stationarity" in sel:
        expl("ARIMA models need constant mean and variance. If revenue is trending up, we difference it: predict the daily change instead of the level.")
        fml("ΔY_t = Y_t − Y_{t-1}    ← predict change, not level")
        if adf_df is not None:
            for _,row in adf_df.iterrows():
                ok="YES" in str(row.get("Stationary",""))
                st.metric(row["Series"],f"p = {row['p_value']:.4f}",delta="✅ Stationary" if ok else "⚠️ Not stationary",delta_color="normal" if ok else "inverse")
        fig_d=make_subplots(rows=2,cols=1,subplot_titles=("Raw revenue","After differencing — bounces around 0"),vertical_spacing=0.14)
        fig_d.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["Revenue_USD"],line=dict(color=BL,width=1.5),fill="tozeroy",fillcolor="rgba(59,111,212,0.07)"),row=1,col=1)
        fig_d.add_trace(go.Scatter(x=feat_df["Date"],y=feat_df["revenue_diff1"],line=dict(color=BY,width=1.5),fill="tozeroy",fillcolor="rgba(245,158,11,0.07)"),row=2,col=1)
        fig_d.add_hline(y=0,line_color="#1a2d4a",line_dash="dash",row=2,col=1)
        fig_d.update_layout(**B,height=380,showlegend=False,margin=dict(l=0,r=0,t=28,b=0))
        st.plotly_chart(fig_d,use_container_width=True)

    elif "VIF" in sel:
        expl("VIF detects when two features say the same thing. High VIF → drop or combine with PCA before building XGBoost.")
        fml("VIF = 1/(1−R²)  ·  >10 = drop feature")
        if vif_df is not None:
            fig_vif=go.Figure(go.Bar(x=vif_df["VIF"],y=vif_df["Feature"],orientation="h",marker_color=["#ef4444" if v>10 else ("#f59e0b" if v>5 else "#22c55e") for v in vif_df["VIF"]],text=[f"{v:.1f}" for v in vif_df["VIF"]],textposition="outside"))
            fig_vif.add_vline(x=5,line_color=BY,line_dash="dot",line_width=1)
            fig_vif.add_vline(x=10,line_color=BR,line_dash="dot",line_width=1)
            fig_vif.update_layout(**B,height=360,title="green=keep · yellow=watch · red=drop",margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_vif,use_container_width=True)


# ═════════════════════════════════════════════════════════════
# GLOSSARY
# ═════════════════════════════════════════════════════════════
elif st.session_state.page=="glossary":
    st.markdown('<div class="pg-title">📖 Glossary</div>',unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Plain-English definitions for every metric and concept in this dashboard. No prior knowledge required.</div>',unsafe_allow_html=True)

    G=[
        ("MAD — Mean Absolute Deviation","How much daily sales vary from the average. High MAD = unpredictable product = needs more safety stock.","MAD = average |daily demand − avg demand|"),
        ("Safety Stock","Buffer inventory to survive demand spikes during supplier lead time. Without it, any spike above average causes a stockout.","Safety Stock = Z × MAD × √(Lead Time)\nZ=1.65 → 95% in-stock rate"),
        ("ROP — Reorder Point","The stock level that triggers a new supplier order. Designed so the order arrives just before safety stock runs out.","ROP = (Avg Daily Demand × Lead Time) + Safety Stock"),
        ("Gross Margin %","What percentage of each sale is profit after subtracting the cost of goods.","Gross Margin = (Retail − Cost) / Retail × 100"),
        ("Sell-Through %","What fraction of available stock was actually sold to customers. Low sell-through = products sitting unsold.","Sell-Through = Units Sold / (Units Sold + Stock) × 100"),
        ("EMA — Exponential Moving Average","A moving average that gives more weight to recent days and less to older ones. Reacts faster than SMA.","EMA_t = α × today + (1−α) × yesterday's EMA\nα = 2 / (window + 1)"),
        ("SMA — Simple Moving Average","Averages the last N days equally. Simple to understand but lags behind sudden changes.","SMA = sum of last N days / N"),
        ("Holt-Winters","Forecasting that tracks level + trend + seasonality simultaneously. Best for retail with weekly cycles.","3 components: Level (α), Trend (β), Seasonality (γ)"),
        ("RFM — Recency, Frequency, Monetary","Customer scoring system. Recency=how recently, Frequency=how often, Monetary=how much. Combined score 3–9 → segments.","RFM Score = R + F + M  (each 1–3)\n8–9=Champion · 6–7=Loyal · 4–5=Potential · 3=At Risk"),
        ("Market Basket / Combo Pairs","Products that appear together in the same order. Used for bundles, promotions, shelf placement.","Lift = P(A and B) / (P(A) × P(B)) · Lift>1 = genuine pair"),
        ("Support","% of all orders containing a specific product or pair.","Support(A,B) = orders with both / total orders"),
        ("Confidence","If customer buys A, probability they also buy B.","Confidence(A→B) = Support(A,B) / Support(A)"),
        ("Lift","How much more likely B is when A is already in the cart vs random chance. Lift=1=no link, Lift=2.5=2.5× more likely.","Lift = Confidence(A→B) / Support(B)"),
        ("Z-Score","How far a value is from the mean in standard deviation units. 0=average, +2=unusually high, −2=unusually low.","Z = (x − μ) / σ"),
        ("Min-Max Scaling","Squeezes all values into 0–1. Used as input to neural networks.","x' = (x − min) / (max − min)"),
        ("Cyclic Time Encoding","Projects days onto a circle so Monday and Sunday are adjacent (not distance 6 apart).","sin_dow = sin(2π × day / 7)\ncos_dow = cos(2π × day / 7)"),
        ("Lag Features","Columns carrying past values forward so a model can 'remember' history.","lag_1 = Revenue.shift(1)  ← yesterday\nlag_7 = Revenue.shift(7)  ← last week"),
        ("Stationarity","Series with constant mean and variance over time. Required for ARIMA.","ADF test: p < 0.05 → stationary ✅"),
        ("First-Order Differencing","Predicts the daily change instead of the raw value. Removes trends to achieve stationarity.","ΔY_t = Y_t − Y_{t-1}"),
        ("VIF — Variance Inflation Factor","Detects redundant features. VIF>10 = two features saying the same thing.","VIF = 1/(1−R²) · >10 = drop feature"),
        # ── SEO terms ────────────────────────────────────────
        ("SEO — Search Engine Optimisation","The practice of making web content easier for search engines to find and rank for specific keywords.","Score 0–100 via density analysis"),
        ("Text Normalisation","Converting raw human text into clean tokens: lowercase → strip punctuation → split → remove stop-words.","re.sub(r'[^a-z0-9\\s]', ' ', text.lower()).split()"),
        ("Keyword Density","How often a keyword appears relative to the total word count. 1 appearance in 100 words = 1%.","Density = (matches / total tokens) × 100"),
        ("Sliding Window N-Gram","A loop that slides a window of N words across the token list to find multi-word keyword phrases.","for i in range(len(tokens) − N + 1): check tokens[i:i+N]"),
        ("Stop Words","Common words (the, and, is, to…) that carry no SEO signal. Stored as a set for O(1) lookup.","O(1) hash lookup vs O(n) list scan"),
        ("SEO Sweet Spot","Keyword density between 1% and 3.5%. Content reads as human-authored; crawler trusts the page.","Score = 100  when  1% ≤ density ≤ 3.5%"),
        ("Keyword Stuffing","Density above 3.5%. Triggers a penalty that accumulates quickly to tank the score before text becomes unreadable.","Score = max(0, int(100 − (excess × 15)))\nexcess = density − 3.5%"),
        ("Density Penalty Multiplier","Factor of 15 applied to excess density. Ensures score tanks meaningfully before copy becomes unreadable.","Penalty = (density − 3.5%) × 15"),
        ("Service Level (inventory)","Target probability of having stock when a customer wants to buy. Z=1.65 → 95%, Z=2.05 → 98%.","Higher level = more safety stock = higher holding cost"),
        ("Lead Time","Days between placing a supplier order and receiving stock. Default = 7 days in this dashboard.","Used in: ROP = (Avg Demand × Lead Time) + Safety Stock"),
    ]

    search=st.text_input("Search","",placeholder="Type any term…")
    filtered=[(t,p,f) for t,p,f in G if search.lower() in t.lower() or search.lower() in p.lower()]
    st.markdown(f"<div style='font-size:11px;color:#1e3a5a;margin-bottom:14px'>{len(filtered)} terms</div>",unsafe_allow_html=True)
    for term,plain,form in filtered:
        st.markdown(f'<div class="gcard"><div class="gcard-term">{term}</div><div class="gcard-plain">{plain}</div><div class="gcard-formula">{form}</div></div>',unsafe_allow_html=True)

st.markdown("<div style='margin-top:44px;padding-top:12px;border-top:1px solid #0d1e38;color:#0d1e38;font-size:10px;text-align:center'>🧭 Navigare · Retail Analytics · Week 7 · Phase 3 · github.com/SS10-code/Navigare</div>",unsafe_allow_html=True)