"""
schema_mapper.py
────────────────────────────────────────────────────────────────
Week 4 — Universal Schema Mapping Contract

Maps BOTH real-world datasets into one unified schema:
  • Olist Brazilian E-Commerce  (BRL → USD)
  • UCI Online Retail II        (GBP → USD)

To use REAL Kaggle data:
  1. Download Olist → point OLIST_PATH to your olist_order_items_dataset.csv
  2. Download UCI   → point UCI_PATH   to your online_retail_II.csv
  The column mapping logic below is identical for both real and synthetic.

Output:
    data/clean/unified_transactions.csv

Run:
    python schema_mapper.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random, os

rng    = np.random.default_rng(42)
random.seed(42)
TODAY  = datetime.today()

BRL_TO_USD = 0.20
GBP_TO_USD = 1.27

os.makedirs("data/clean",     exist_ok=True)
os.makedirs("data/synthetic", exist_ok=True)

OLIST_PATH   = "data/synthetic/olist_simulated.csv"
UCI_PATH     = "data/synthetic/uci_simulated.csv"
UNIFIED_PATH = "data/clean/unified_transactions.csv"

RESAMPLING_RULES = """
RESAMPLING LOGIC RULES
═══════════════════════════════════════════════════════════════
R-01  NEGATIVE QUANTITY → DROP
      UCI returns appear as negative qty. Exclude from sales analytics.
      df = df[df["Quantity"] > 0]

R-02  MISSING PRICE → FILL WITH CATEGORY MEDIAN
      df["Item_Price_USD"].fillna(
          df.groupby("Category")["Item_Price_USD"].transform("median"))

R-03  MISSING DATE → DROP ROW
      Cannot place on time axis. df = df.dropna(subset=["Transaction_Date"])

R-04  TIME-SERIES PADDING
      After daily groupby, resample("D").sum().fillna(0)
      Missing days = 0, NOT NaN. NaN breaks SMA rolling + HW seasonal fit.

R-05  CURRENCY STANDARDIZATION
      BRL × 0.20 → USD  |  GBP × 1.27 → USD

R-06  DUPLICATE TXN+PRODUCT → KEEP FIRST
      df.drop_duplicates(subset=["Transaction_ID","Product_ID"], keep="first")
═══════════════════════════════════════════════════════════════
"""


def simulate_olist(n=500) -> pd.DataFrame:
    product_pool = [f"PROD-BR-{i:03d}" for i in range(1, 41)]
    base = TODAY - timedelta(days=365)
    rows = []
    for i in range(n):
        ts = base + timedelta(days=int(rng.integers(0,364)),
                              hours=int(rng.integers(8,21)),
                              minutes=int(rng.integers(0,59)))
        rows.append({
            "order_id":                 f"ORD-BR-{i+1:05d}",
            "customer_id":              f"CUST-BR-{rng.integers(1,81):04d}",
            "product_id":               random.choice(product_pool),
            "price":                    round(float(rng.uniform(15.0, 450.0)), 2),
            "order_purchase_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "order_item_id":            int(rng.integers(1, 4)),
            "product_category_name":    random.choice(
                ["utilidades_domesticas","eletronicos","alimentos","moda","esportes"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OLIST_PATH, index=False)
    print(f"  [SIM] Olist → {len(df)} rows")
    return df


def simulate_uci(n=600) -> pd.DataFrame:
    stock_pool = [(f"SC{i:05d}", f"Product {chr(65+i%26)}-{i}") for i in range(1,51)]
    base = TODAY - timedelta(days=365)
    rows = []
    for i in range(n):
        sc, desc = random.choice(stock_pool)
        ts = base + timedelta(days=int(rng.integers(0,364)),
                              hours=int(rng.integers(9,18)),
                              minutes=int(rng.integers(0,59)))
        qty = int(rng.integers(1,25))
        if rng.random() < 0.03:
            qty = -qty
        rows.append({
            "Invoice":     f"INV-{500000+i}",
            "StockCode":   sc, "Description": desc,
            "Quantity":    qty,
            "InvoiceDate": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Price":       round(float(rng.uniform(0.50, 25.0)), 2),
            "Customer ID": f"CUST-UK-{int(rng.integers(10000,18000))}",
            "Country":     random.choice(["United Kingdom","Germany","France","Spain"]),
        })
    df = pd.DataFrame(rows)
    df.to_csv(UCI_PATH, index=False)
    print(f"  [SIM] UCI   → {len(df)} rows")
    return df


def map_olist(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Store_Type"]       = "E-Commerce"
    out["Transaction_ID"]   = df["order_id"]
    out["Customer_ID"]      = df["customer_id"]
    out["Product_ID"]       = df["product_id"]
    out["Source_Price"]     = df["price"]
    out["Source_Currency"]  = "BRL"
    out["Item_Price_USD"]   = (df["price"] * BRL_TO_USD).round(2)
    out["Quantity"]         = df["order_item_id"]
    out["Line_Total_USD"]   = (out["Item_Price_USD"] * out["Quantity"]).round(2)
    ts = pd.to_datetime(df["order_purchase_timestamp"])
    out["Transaction_Date"] = ts.dt.date.astype(str)
    out["Transaction_Time"] = ts.dt.strftime("%H:%M")
    out["Category"]         = df["product_category_name"]
    out["Country"]          = "Brazil"
    return out


def map_uci(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["Quantity"] > 0].copy()   # R-01
    out = pd.DataFrame()
    out["Store_Type"]       = "Brick-and-Mortar"
    out["Transaction_ID"]   = df["Invoice"].values
    out["Customer_ID"]      = df["Customer ID"].values
    out["Product_ID"]       = df["StockCode"].values
    out["Source_Price"]     = df["Price"].values
    out["Source_Currency"]  = "GBP"
    out["Item_Price_USD"]   = (df["Price"] * GBP_TO_USD).round(2)
    out["Quantity"]         = df["Quantity"].values
    out["Line_Total_USD"]   = (out["Item_Price_USD"] * out["Quantity"]).round(2)
    ts = pd.to_datetime(df["InvoiceDate"])
    out["Transaction_Date"] = ts.dt.date.astype(str)
    out["Transaction_Time"] = ts.dt.strftime("%H:%M")
    out["Category"]         = df["Description"].values
    out["Country"]          = df["Country"].values
    return out


def run():
    print("\n🗺️   Schema Mapper — Week 4")
    print("=" * 45)
    print(RESAMPLING_RULES)

    olist = simulate_olist(500)
    uci   = simulate_uci(600)

    olist_m = map_olist(olist)
    uci_m   = map_uci(uci)
    print(f"  Olist mapped : {len(olist_m)} rows")
    print(f"  UCI mapped   : {len(uci_m)} rows (negatives dropped)")

    unified = pd.concat([olist_m, uci_m], ignore_index=True)
    unified = unified.dropna(subset=["Transaction_Date"])            # R-03
    unified["Item_Price_USD"] = unified["Item_Price_USD"].fillna(    # R-02
        unified.groupby("Category")["Item_Price_USD"].transform("median"))
    unified = unified.drop_duplicates(                               # R-06
        subset=["Transaction_ID","Product_ID"], keep="first")
    unified["Transaction_Date"] = pd.to_datetime(unified["Transaction_Date"])
    unified = unified.sort_values("Transaction_Date").reset_index(drop=True)

    unified.to_csv(UNIFIED_PATH, index=False)
    print(f"\n  Final rows   : {len(unified)}")
    print(f"  Date range   : {unified['Transaction_Date'].min().date()} → {unified['Transaction_Date'].max().date()}")
    print(f"  Revenue USD  : ${unified['Line_Total_USD'].sum():,.2f}")
    print(f"\n✅  Saved → {UNIFIED_PATH}\n")
    return unified


if __name__ == "__main__":
    run()