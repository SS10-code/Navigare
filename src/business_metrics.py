"""
business_metrics.py
────────────────────────────────────────────────────────────────
Week 6 — Deterministic Rule-Based Business Metric Engine

All calculations are rule-based (no ML). They run on any valid
Transactions + Inventory CSV that follows the Navigare schema.

Metrics computed:
  1.  MAD              — Mean Absolute Deviation of daily demand
  2.  Safety Stock     — Buffer stock to survive demand spikes
  3.  ROP              — Reorder Point (when to place an order)
  4.  Gross Margin     — Revenue minus cost, per product
  5.  Sell-Through %   — How much of received stock was sold
  6.  Revenue / Day    — Normalised daily revenue per product
  7.  RFM Scores       — Recency, Frequency, Monetary per customer
  8.  Combo Logic      — Market basket pairs (what sells together)

Output:
    data/clean/inventory_metrics.csv     ← MAD, Safety Stock, ROP
    data/clean/customer_rfm.csv          ← RFM scores
    data/clean/combo_pairs.csv           ← Market basket pairs
    data/clean/product_metrics.csv       ← Margin, sell-through

Run:
    python business_metrics.py
"""

import pandas as pd
import numpy as np
from itertools import combinations
import os, warnings
warnings.filterwarnings("ignore")

os.makedirs("data/clean", exist_ok=True)

INV_PATH = "data/raw/inventory.csv"
TXN_PATH = "data/raw/transactions.csv"
CST_PATH = "data/raw/customers.csv"


# ═══════════════════════════════════════════════════════════════
# LOAD & VALIDATE
# ═══════════════════════════════════════════════════════════════

def load_and_validate():
    """
    Loads both tables and runs defensive checks.
    Raises clear errors if required columns are missing.
    Handles common entry typos (extra spaces, mixed case).
    """
    print("📂  Loading tables...")

    # ── Inventory ─────────────────────────────────────────────
    if not os.path.exists(INV_PATH):
        raise FileNotFoundError(f"Missing: {INV_PATH}  →  run generate_mock_data.py first")
    inv = pd.read_csv(INV_PATH)

    # Defensive: strip whitespace from string columns (common typo source)
    for col in inv.select_dtypes("object").columns:
        inv[col] = inv[col].str.strip()

    inv_required = ["Product_ID","Cost_Price","Retail_Price","Current_Stock","Reorder_Level"]
    missing_inv  = [c for c in inv_required if c not in inv.columns]
    if missing_inv:
        raise ValueError(f"Inventory missing columns: {missing_inv}")

    # Defensive: fix negative stock (data entry error → clamp to 0)
    neg_stock = (inv["Current_Stock"] < 0).sum()
    if neg_stock:
        print(f"  ⚠️  Fixing {neg_stock} negative stock values → 0")
        inv.loc[inv["Current_Stock"] < 0, "Current_Stock"] = 0

    # Defensive: fix price inversions (retail < cost → set to cost × 1.5)
    price_inv = (inv["Retail_Price"] <= inv["Cost_Price"]).sum()
    if price_inv:
        print(f"  ⚠️  Fixing {price_inv} price inversions → cost × 1.5")
        mask = inv["Retail_Price"] <= inv["Cost_Price"]
        inv.loc[mask, "Retail_Price"] = (inv.loc[mask, "Cost_Price"] * 1.5).round(2)

    print(f"  ✅ Inventory: {len(inv)} rows, {inv['Product_ID'].nunique()} SKUs")

    # ── Transactions ──────────────────────────────────────────
    if not os.path.exists(TXN_PATH):
        raise FileNotFoundError(f"Missing: {TXN_PATH}  →  run generate_mock_data.py first")
    txn = pd.read_csv(TXN_PATH, parse_dates=["Transaction_Date"])

    for col in txn.select_dtypes("object").columns:
        txn[col] = txn[col].str.strip()

    txn_required = ["Transaction_ID","Product_ID","Quantity","Unit_Price","Line_Total","Transaction_Date"]
    missing_txn  = [c for c in txn_required if c not in txn.columns]
    if missing_txn:
        raise ValueError(f"Transactions missing columns: {missing_txn}")

    # Defensive: drop returns (negative quantity)
    returns = (txn["Quantity"] < 0).sum()
    if returns:
        print(f"  ⚠️  Dropping {returns} return rows (negative quantity)")
        txn = txn[txn["Quantity"] > 0].copy()

    # Defensive: drop rows with null dates
    null_dates = txn["Transaction_Date"].isna().sum()
    if null_dates:
        print(f"  ⚠️  Dropping {null_dates} rows with null Transaction_Date")
        txn = txn.dropna(subset=["Transaction_Date"])

    # Defensive: drop duplicate transaction + product combos
    before = len(txn)
    txn = txn.drop_duplicates(subset=["Transaction_ID","Product_ID"], keep="first")
    dupes = before - len(txn)
    if dupes:
        print(f"  ⚠️  Dropped {dupes} duplicate Transaction_ID+Product_ID rows")

    print(f"  ✅ Transactions: {len(txn)} rows, "
          f"{txn['Transaction_Date'].min().date()} → {txn['Transaction_Date'].max().date()}")

    # ── Customers ─────────────────────────────────────────────
    cst = pd.read_csv(CST_PATH) if os.path.exists(CST_PATH) else None
    if cst is not None:
        for col in cst.select_dtypes("object").columns:
            cst[col] = cst[col].str.strip()
        print(f"  ✅ Customers: {len(cst)} rows")

    return inv, txn, cst


# ═══════════════════════════════════════════════════════════════
# 1. MAD — MEAN ABSOLUTE DEVIATION
# ═══════════════════════════════════════════════════════════════
# MAD measures how much daily demand fluctuates.
#
# Why MAD instead of Std Dev?
#   MAD uses absolute values — it's more robust to outlier sales days
#   (e.g. a holiday spike) and easier to explain to a store owner:
#   "On average, demand varies by ±X units per day."
#
# Formula: MAD = (1/n) × Σ |demand_i − avg_demand|
#
# Why it matters:
#   High MAD = volatile product → needs more safety stock
#   Low MAD  = predictable product → can run leaner inventory

def compute_mad(txn: pd.DataFrame, inv: pd.DataFrame) -> pd.DataFrame:
    print("\n── Computing MAD (Mean Absolute Deviation) ──")

    all_dates  = pd.date_range(txn["Transaction_Date"].min(),
                               txn["Transaction_Date"].max(), freq="D")
    results    = []

    for _, prod_row in inv.iterrows():
        pid      = prod_row["Product_ID"]
        prod_txn = txn[txn["Product_ID"] == pid]

        # Daily demand — R-04: fill missing days with 0
        daily_demand = (
            prod_txn.groupby("Transaction_Date")["Quantity"]
            .sum()
            .reindex(all_dates, fill_value=0)
        )

        avg_demand = daily_demand.mean()
        mad        = (daily_demand - avg_demand).abs().mean()
        std_demand = daily_demand.std()
        max_demand = daily_demand.max()
        days_w_sales = (daily_demand > 0).sum()

        results.append({
            "Product_ID":       pid,
            "Product_Name":     prod_row.get("Product_Name",""),
            "Category":         prod_row.get("Category",""),
            "Avg_Daily_Demand": round(avg_demand, 3),
            "MAD":              round(mad, 3),
            "Std_Demand":       round(std_demand, 3),
            "Max_Daily_Demand": int(max_demand),
            "Days_With_Sales":  int(days_w_sales),
            "Total_Days":       len(all_dates),
            "Demand_CV":        round(mad / avg_demand if avg_demand > 0 else 0, 3),
        })
        # Coefficient of Variation = MAD/Mean — normalises volatility across products

    df = pd.DataFrame(results)
    print(f"  MAD range: {df['MAD'].min():.2f} → {df['MAD'].max():.2f} units/day")
    print(f"  Most volatile: {df.loc[df['MAD'].idxmax(),'Product_Name']} (MAD={df['MAD'].max():.2f})")
    print(f"  Most stable:   {df.loc[df['MAD'].idxmin(),'Product_Name']} (MAD={df['MAD'].min():.2f})")
    return df


# ═══════════════════════════════════════════════════════════════
# 2. SAFETY STOCK
# ═══════════════════════════════════════════════════════════════
# Safety Stock is the buffer kept to absorb demand spikes during
# the lead time (how long it takes for a supplier order to arrive).
#
# Formula (MAD-based, more robust than std-dev formula):
#   Safety Stock = Z × MAD × √(Lead_Time)
#
# Z = service level multiplier
#   Z = 1.28  → 90% service level (10% chance of stockout)
#   Z = 1.65  → 95% service level (5% chance of stockout)
#   Z = 2.05  → 98% service level (2% chance of stockout)
#
# √(Lead_Time): amplifies uncertainty — a 7-day lead time is
# more uncertain than a 1-day lead time; square root dampens
# this so it doesn't over-stock unrealistically.

def compute_safety_stock(mad_df: pd.DataFrame,
                         lead_time_days: int = 7,
                         service_level_z: float = 1.65) -> pd.DataFrame:
    print(f"\n── Computing Safety Stock (Z={service_level_z}, Lead={lead_time_days}d) ──")

    df = mad_df.copy()
    df["Lead_Time_Days"]    = lead_time_days
    df["Service_Level_Z"]   = service_level_z

    # Core formula: Z × MAD × sqrt(Lead_Time)
    df["Safety_Stock"]      = (service_level_z * df["MAD"] * np.sqrt(lead_time_days)).round(1)
    df["Safety_Stock_Low"]  = (1.28 * df["MAD"] * np.sqrt(lead_time_days)).round(1)   # 90%
    df["Safety_Stock_High"] = (2.05 * df["MAD"] * np.sqrt(lead_time_days)).round(1)   # 98%

    print(f"  Safety stock range: {df['Safety_Stock'].min()} → {df['Safety_Stock'].max()} units")
    return df


# ═══════════════════════════════════════════════════════════════
# 3. REORDER POINT (ROP)
# ═══════════════════════════════════════════════════════════════
# ROP answers: "At what stock level should I place a new order?"
#
# Formula:
#   ROP = (Avg_Daily_Demand × Lead_Time) + Safety_Stock
#
# Intuition:
#   - Left side: how much stock you expect to sell during the
#     time it takes for your order to arrive
#   - Right side: buffer for demand spikes during that window
#
# When Current_Stock drops to ROP → place a reorder immediately.
# If you wait until stock = 0, the safety stock won't help you.

def compute_rop(ss_df: pd.DataFrame, inv: pd.DataFrame) -> pd.DataFrame:
    print("\n── Computing ROP (Reorder Point) ──")

    df = ss_df.copy()
    lt = df["Lead_Time_Days"]

    df["ROP"]            = ((df["Avg_Daily_Demand"] * lt) + df["Safety_Stock"]).round(1)
    df["ROP_Low"]        = ((df["Avg_Daily_Demand"] * lt) + df["Safety_Stock_Low"]).round(1)
    df["ROP_High"]       = ((df["Avg_Daily_Demand"] * lt) + df["Safety_Stock_High"]).round(1)

    # Join current stock to flag which products need ordering NOW
    inv_slim = inv[["Product_ID","Current_Stock","Reorder_Level"]].copy()
    df = df.merge(inv_slim, on="Product_ID", how="left")

    df["Order_Now"]      = (df["Current_Stock"] <= df["ROP"]).astype(int)
    df["Units_Below_ROP"]= (df["ROP"] - df["Current_Stock"]).clip(lower=0).round(1)

    n_order = df["Order_Now"].sum()
    print(f"  Products to reorder NOW (stock ≤ ROP): {n_order}")
    print(f"  Products with safe stock levels:        {len(df) - n_order}")
    return df


# ═══════════════════════════════════════════════════════════════
# 4. PRODUCT BUSINESS METRICS
# ═══════════════════════════════════════════════════════════════
# Gross Margin % — how much of each sale is profit
# Sell-Through % — what fraction of available stock was sold
# Revenue / Day  — average daily revenue contribution

def compute_product_metrics(txn: pd.DataFrame, inv: pd.DataFrame) -> pd.DataFrame:
    print("\n── Computing Product Business Metrics ──")

    days_in_period = (txn["Transaction_Date"].max() - txn["Transaction_Date"].min()).days + 1

    prod_txn = txn.groupby("Product_ID").agg(
        Total_Units_Sold  = ("Quantity",    "sum"),
        Total_Revenue     = ("Line_Total",  "sum"),
        Num_Transactions  = ("Transaction_ID","nunique"),
    ).reset_index()

    df = inv.merge(prod_txn, on="Product_ID", how="left").fillna(0)

    df["Gross_Margin_Pct"] = ((df["Retail_Price"] - df["Cost_Price"]) / df["Retail_Price"] * 100).round(1)
    df["Gross_Profit_Per_Unit"] = (df["Retail_Price"] - df["Cost_Price"]).round(2)
    df["Revenue_Per_Day"]  = (df["Total_Revenue"] / days_in_period).round(2)
    df["Units_Per_Day"]    = (df["Total_Units_Sold"] / days_in_period).round(2)

    # Sell-Through %: units sold / (units sold + current stock)
    # Represents what % of total available inventory moved through to customers
    df["Sell_Through_Pct"] = (
        df["Total_Units_Sold"] /
        (df["Total_Units_Sold"] + df["Current_Stock"]).replace(0, np.nan)
        * 100
    ).round(1).fillna(0)

    keep = ["Product_ID","Product_Name","Category","Cost_Price","Retail_Price",
            "Gross_Margin_Pct","Gross_Profit_Per_Unit","Current_Stock",
            "Total_Units_Sold","Total_Revenue","Revenue_Per_Day","Units_Per_Day",
            "Sell_Through_Pct","Num_Transactions"]
    df = df[[c for c in keep if c in df.columns]]

    best_margin = df.loc[df["Gross_Margin_Pct"].idxmax(), "Product_Name"]
    best_revenue = df.loc[df["Total_Revenue"].idxmax(), "Product_Name"]
    print(f"  Best margin:  {best_margin} ({df['Gross_Margin_Pct'].max():.1f}%)")
    print(f"  Best revenue: {best_revenue} (${df['Total_Revenue'].max():,.2f})")

    out_path = "data/clean/product_metrics.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved → {out_path}")
    return df


# ═══════════════════════════════════════════════════════════════
# 5. RFM — CUSTOMER SCORING
# ═══════════════════════════════════════════════════════════════
# Recency   — How recently did they buy? (days since last purchase)
# Frequency — How often do they buy?    (number of transactions)
# Monetary  — How much do they spend?   (total revenue)
#
# Each scored 1–3 (3=best), combined into a label.
# Purpose: identify who your best customers are so you can
# focus loyalty rewards and marketing on them.

def compute_rfm(txn: pd.DataFrame) -> pd.DataFrame:
    print("\n── Computing RFM Customer Scores ──")

    snapshot_date = txn["Transaction_Date"].max() + pd.Timedelta(days=1)

    rfm = txn.groupby("Customer_ID").agg(
        Last_Purchase   = ("Transaction_Date", "max"),
        Frequency       = ("Transaction_ID",   "nunique"),
        Monetary        = ("Line_Total",        "sum"),
    ).reset_index()

    rfm["Recency_Days"] = (snapshot_date - rfm["Last_Purchase"]).dt.days

    # Score 1–3 using quantile-based bins (equal thirds)
    rfm["R_Score"] = pd.qcut(rfm["Recency_Days"],  q=3, labels=[3,2,1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), q=3, labels=[1,2,3]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"),  q=3, labels=[1,2,3]).astype(int)
    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    def label(score):
        if score >= 8: return "Champion"
        if score >= 6: return "Loyal"
        if score >= 4: return "Potential"
        return "At Risk"

    rfm["Segment"]     = rfm["RFM_Score"].apply(label)
    rfm["Last_Purchase"] = rfm["Last_Purchase"].dt.date
    rfm["Monetary"]    = rfm["Monetary"].round(2)

    seg_counts = rfm["Segment"].value_counts()
    for seg, count in seg_counts.items():
        print(f"  {seg:12s}: {count} customers")

    out_path = "data/clean/customer_rfm.csv"
    rfm.to_csv(out_path, index=False)
    print(f"  Saved → {out_path}")
    return rfm


# ═══════════════════════════════════════════════════════════════
# 6. COMBO LOGIC — MARKET BASKET ANALYSIS
# ═══════════════════════════════════════════════════════════════
# Finds product pairs that frequently appear in the same order.
#
# Metrics:
#   Support     = (orders with both A and B) / total orders
#                 How often this pair appears overall
#   Confidence  = support(A,B) / support(A)
#                 If someone buys A, probability they also buy B
#   Lift        = confidence / support(B)
#                 How much more likely B is bought with A vs. randomly
#                 Lift > 1 = genuine association (not just popular items)
#
# Scalability note:
#   With 25 products → C(25,2) = 300 pairs — manageable.
#   With 1000 products → C(1000,2) = 499,500 pairs — need Apriori/FP-Growth.
#   This rule-based implementation uses a min_support threshold to prune
#   before the pair count explodes.

def compute_combo_pairs(txn: pd.DataFrame,
                        min_support: float = 0.02,
                        top_n: int = 30) -> pd.DataFrame:
    print("\n── Computing Combo Pairs (Market Basket) ──")

    # Build order → product set mapping
    orders = txn.groupby("Transaction_ID")["Product_ID"].apply(set).reset_index()
    orders.columns = ["Transaction_ID","Products"]
    total_orders = len(orders)
    print(f"  Total orders: {total_orders}  |  min_support: {min_support:.0%}")

    # Count individual product support
    product_support = {}
    for products in orders["Products"]:
        for p in products:
            product_support[p] = product_support.get(p, 0) + 1

    # Count pair co-occurrences (only orders with ≥2 products)
    pair_counts = {}
    multi_item  = orders[orders["Products"].apply(len) >= 2]
    for products in multi_item["Products"]:
        for pair in combinations(sorted(products), 2):
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

    print(f"  Pairs found: {len(pair_counts)}")

    # Build results — filter by min_support
    results = []
    for (pa, pb), count in pair_counts.items():
        support    = count / total_orders
        if support < min_support:
            continue
        conf_a_b   = count / product_support.get(pa, 1)
        conf_b_a   = count / product_support.get(pb, 1)
        sup_b      = product_support.get(pb, 1) / total_orders
        lift       = conf_a_b / sup_b if sup_b > 0 else 0
        results.append({
            "Product_A_ID":   pa,
            "Product_B_ID":   pb,
            "Co_Occurrences": count,
            "Support":        round(support, 4),
            "Confidence_AB":  round(conf_a_b, 4),
            "Confidence_BA":  round(conf_b_a, 4),
            "Lift":           round(lift, 3),
        })

    df = pd.DataFrame(results).sort_values("Lift", ascending=False).head(top_n)

    # Join product names for readability
    name_map = txn[["Product_ID","Product_Name"]].drop_duplicates().set_index("Product_ID")["Product_Name"]
    df["Product_A"] = df["Product_A_ID"].map(name_map)
    df["Product_B"] = df["Product_B_ID"].map(name_map)
    df["Pair_Label"] = df["Product_A"] + "  +  " + df["Product_B"]

    df = df[["Pair_Label","Product_A","Product_B","Co_Occurrences",
             "Support","Confidence_AB","Lift"]].reset_index(drop=True)

    print(f"  Pairs above support threshold: {len(df)}")
    if len(df):
        top = df.iloc[0]
        print(f"  Top pair: {top['Pair_Label']}  (Lift={top['Lift']:.2f})")

    # Scalability note stored in file header via a metadata row approach
    out_path = "data/clean/combo_pairs.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved → {out_path}")
    print(f"  Scalability: {len(txn['Product_ID'].unique())} SKUs → "
          f"C({len(txn['Product_ID'].unique())},2) = "
          f"{len(txn['Product_ID'].unique())*(len(txn['Product_ID'].unique())-1)//2} pairs "
          f"(manageable). At 500+ SKUs, switch to FP-Growth.")
    return df


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n📊  Business Metrics Engine — Week 6")
    print("=" * 55)

    inv, txn, cst = load_and_validate()

    # Run all metric computations
    mad_df  = compute_mad(txn, inv)
    ss_df   = compute_safety_stock(mad_df, lead_time_days=7, service_level_z=1.65)
    rop_df  = compute_rop(ss_df, inv)
    prod_df = compute_product_metrics(txn, inv)
    rfm_df  = compute_rfm(txn)
    combo_df= compute_combo_pairs(txn, min_support=0.02, top_n=30)

    # Save the master inventory metrics file (MAD + Safety Stock + ROP + current stock)
    inv_metrics = rop_df[[
        "Product_ID","Product_Name","Category",
        "Avg_Daily_Demand","MAD","Std_Demand","Demand_CV",
        "Safety_Stock","Safety_Stock_Low","Safety_Stock_High",
        "ROP","ROP_Low","ROP_High",
        "Lead_Time_Days","Service_Level_Z",
        "Current_Stock","Reorder_Level",
        "Order_Now","Units_Below_ROP",
    ]]
    inv_metrics.to_csv("data/clean/inventory_metrics.csv", index=False)
    print(f"\n  Master inventory metrics → data/clean/inventory_metrics.csv")

    print("\n" + "=" * 55)
    print("✅  All business metrics computed and saved.")
    print("\n  Files written:")
    for f in ["data/clean/inventory_metrics.csv","data/clean/product_metrics.csv",
              "data/clean/customer_rfm.csv","data/clean/combo_pairs.csv"]:
        size = os.path.getsize(f) if os.path.exists(f) else 0
        print(f"    {f}  ({size:,} bytes)")
    print()
