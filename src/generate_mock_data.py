"""
generate_mock_data.py
────────────────────────────────────────────────────────────────
Run FIRST — seeds all raw data files the pipeline depends on.

Output:
    data/raw/inventory.csv
    data/raw/transactions.csv
    data/raw/customers.csv

Usage:
    python generate_mock_data.py
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from faker import Faker
import os

Faker.seed(42)
random.seed(42)
rng   = np.random.default_rng(42)
fake  = Faker()
TODAY = datetime.today().date()

os.makedirs("data/raw", exist_ok=True)

# ── Product master ────────────────────────────────────────────
PRODUCTS = [
    (1,"CF-001","Croissant","Pastries",1.20,3.50),
    (2,"CF-002","Muffin Blueberry","Pastries",0.80,2.75),
    (3,"CF-003","Cinnamon Roll","Pastries",1.10,3.25),
    (4,"CF-004","Danish Almond","Pastries",1.30,3.75),
    (5,"CF-005","Scone Cranberry","Pastries",0.90,2.50),
    (6,"BR-001","Sourdough Loaf","Breads",2.50,7.50),
    (7,"BR-002","Baguette","Breads",1.00,3.50),
    (8,"BR-003","Whole Wheat Loaf","Breads",2.20,6.50),
    (9,"BR-004","Rye Bread","Breads",2.80,7.00),
    (10,"BR-005","Focaccia Herb","Breads",2.00,6.00),
    (11,"CK-001","Birthday Cake 8in","Cakes",8.00,32.00),
    (12,"CK-002","Cheesecake Slice","Cakes",3.00,7.50),
    (13,"CK-003","Carrot Cake","Cakes",3.50,8.50),
    (14,"CK-004","Red Velvet Slice","Cakes",3.20,7.00),
    (15,"CK-005","Tiramisu Cup","Cakes",2.50,6.00),
    (16,"DR-001","Drip Coffee","Drinks",0.30,2.50),
    (17,"DR-002","Latte 16oz","Drinks",0.60,4.75),
    (18,"DR-003","Matcha Latte","Drinks",0.80,5.50),
    (19,"DR-004","Cold Brew","Drinks",0.50,4.25),
    (20,"DR-005","Hot Chocolate","Drinks",0.70,4.00),
    (21,"SV-001","Quiche Lorraine","Savory",2.50,7.50),
    (22,"SV-002","Spinach Wrap","Savory",1.80,6.50),
    (23,"SV-003","Turkey Panini","Savory",2.20,7.00),
    (24,"SV-004","Caprese Sandwich","Savory",2.00,6.75),
    (25,"SV-005","Breakfast Burrito","Savory",1.90,6.25),
]

def gen_inventory():
    rows = []
    for pid, sku, name, cat, cost, retail in PRODUCTS:
        stock    = random.choice([random.randint(1,8), random.randint(10,80)])
        dead     = random.random() < 0.15
        days_ago = random.randint(65,180) if dead else random.randint(0,55)
        lsd      = (TODAY - timedelta(days=days_ago)).isoformat()
        rows.append({
            "Product_ID":     pid,    "SKU":         sku,
            "Product_Name":   name,   "Category":    cat,
            "Cost_Price":     cost,   "Retail_Price": retail,
            "Margin_Pct":     round((retail-cost)/retail*100,1),
            "Current_Stock":  stock,  "Reorder_Level": 10,
            "Low_Stock_Flag": int(stock < 10),
            "Last_Sold_Date": lsd,
            "Dead_Stock_Flag":int(days_ago > 60),
            "Supplier": fake.company(), "Active": "YES",
        })
    df = pd.DataFrame(rows)
    df.to_csv("data/raw/inventory.csv", index=False)
    print(f"  ✅ inventory.csv      → {len(df)} rows")
    return df

def gen_transactions(n_orders=300):
    customer_ids = [f"C{i:04d}" for i in range(1,61)]
    payment_opts = ["Cash","Card","Contactless","Gift Card"]
    base_date    = TODAY - timedelta(days=90)
    rows, txn_id = [], 1
    for _ in range(n_orders):
        cust = random.choice(customer_ids)
        ts   = datetime.combine(base_date + timedelta(days=random.randint(0,89)),
                                datetime.min.time()) + timedelta(
                                    hours=random.randint(7,19), minutes=random.randint(0,59))
        for pid, sku, name, _, _, retail in random.sample(PRODUCTS, k=random.randint(1,4)):
            qty  = random.randint(1,5)
            disc = round(random.choice([0,0,0,0.05,0.10])*retail, 2)
            rows.append({
                "Transaction_ID":   f"TXN-{txn_id:05d}",
                "Customer_ID":      cust,
                "Transaction_Date": ts.date().isoformat(),
                "Transaction_Time": ts.strftime("%H:%M"),
                "Product_ID": pid, "SKU": sku, "Product_Name": name,
                "Quantity": qty, "Unit_Price": retail,
                "Discount": disc,
                "Line_Total": round((retail-disc)*qty, 2),
                "Payment_Method": random.choice(payment_opts),
                "Store_ID": "STORE-01",
            })
        txn_id += 1
    df = pd.DataFrame(rows)
    df.to_csv("data/raw/transactions.csv", index=False)
    print(f"  ✅ transactions.csv   → {len(df)} rows ({n_orders} orders)")
    return df

def gen_customers():
    tiers = ["Bronze","Silver","Gold","Platinum"]
    rows  = []
    for i in range(1,61):
        join = TODAY - timedelta(days=random.randint(30,730))
        rows.append({
            "Customer_ID":  f"C{i:04d}",
            "First_Name":   fake.first_name(), "Last_Name": fake.last_name(),
            "Email":        fake.email(),       "City":      fake.city(),
            "State":        fake.state_abbr(),  "Join_Date": join.isoformat(),
            "Loyalty_Tier": random.choice(tiers),
        })
    df = pd.DataFrame(rows)
    df.to_csv("data/raw/customers.csv", index=False)
    print(f"  ✅ customers.csv      → {len(df)} rows")
    return df

if __name__ == "__main__":
    print("\n🏪  Navigare — Mock Data Generator")
    print("=" * 42)
    inv = gen_inventory()
    txn = gen_transactions(300)
    cst = gen_customers()
    print(f"\n  Low-stock  : {inv['Low_Stock_Flag'].sum()} SKUs")
    print(f"  Dead-stock : {inv['Dead_Stock_Flag'].sum()} SKUs")
    print(f"  Revenue    : ${txn['Line_Total'].sum():,.2f}")
    print(f"\n✅  All raw CSVs ready → data/raw/\n")
