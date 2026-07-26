"""
inventory_health.py
────────────────────────────────────────────────────────────────
Week 8 — Inventory Health Score Engine

Implements the three mathematical constructs from the session:

1. H(x) — Asymmetric Row-Wise Health Function
   Applied to each stock value (the current stock column vector x)
   Returns a health score 0–100 per SKU

2. Aggregate Reduction  μ = (1/N) Σ h_i
   Column-wise arithmetic mean across the health vector h
   Gives the single macroscopic wellness index for the whole store

3. Boolean Masking Matrix  M_i = {1 if status == "CRISIS", 0 otherwise}
   Dynamically pulls out-of-stock and critical items
   Enables the priority alert dispatch system

Defensive Guard Wall:
   N = 0  → Display safe UI, halt math operations
   N > 0  → Run row-vector formulas, dispatch priority alerts
"""

import pandas as pd
import numpy as np
from typing import Optional
import os

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

# H(x) scoring thresholds — tunable
CRISIS_THRESHOLD    = 0      # stock = 0   → score 0   (out of stock, immediate loss)
CRITICAL_THRESHOLD  = 5      # stock 1–5   → score 20  (hours from stockout)
LOW_THRESHOLD       = 10     # stock 6–10  → score 45  (below reorder point)
WARNING_THRESHOLD   = 20     # stock 11–20 → score 70  (approaching low)
HEALTHY_THRESHOLD   = 50     # stock 21–50 → score 88  (healthy)
# stock > 50                              → score 100 (overstock risk begins)
OVERSTOCK_THRESHOLD = 100    # stock > 100 → holding cost penalty kicks in
OVERSTOCK_PENALTY   = 0.15   # 15% score deduction per 10 units over threshold

STATUS_LABELS = {
    (0,   0):   ("CRISIS",   0,   "#ef4444"),   # out of stock
    (1,   5):   ("CRITICAL", 20,  "#f97316"),   # hours from stockout
    (6,   10):  ("LOW",      45,  "#eab308"),   # below ROP
    (11,  20):  ("WARNING",  70,  "#84cc16"),   # approaching low
    (21,  50):  ("HEALTHY",  88,  "#22c55e"),   # good
    (51,  100): ("OPTIMAL",  100, "#06b6d4"),   # ideal range
    (101, 9999):("OVERSTOCK",75,  "#a855f7"),   # capital tied up
}


# ─────────────────────────────────────────────────────────────
# 1.  H(x) — ASYMMETRIC HEALTH FUNCTION
# ─────────────────────────────────────────────────────────────

def H(x: float, reorder_level: float = 10.0) -> dict:
    """
    Asymmetric inventory health function applied row-wise to each SKU.

    Why asymmetric?
    The cost of being out of stock is NOT symmetric with the cost of having
    too much stock. Running out causes immediate sale loss + long-term
    customer retention decay. Overstocking ties up capital and creates
    physical liabilities (warehouse space, degradation, expiry).

    The function is therefore NOT a simple linear scale — it applies a
    steep penalty below the reorder point and a softer penalty above the
    overstock threshold.

    Args:
        x:             Current stock units for one SKU
        reorder_level: The ROP for this SKU (default 10)

    Returns:
        dict with score 0–100, status label, color, and explanation
    """
    x = max(0, float(x))   # defensive: clamp negatives (Chaos Monkey residue)

    if x == 0:
        return {"score": 0,   "status": "CRISIS",   "color": "#ef4444",
                "explanation": "ZERO STOCK — sales impossible. Immediate reorder required."}

    elif x <= 5:
        # Linear interpolation 0→20 for stock 1→5
        score = int((x / 5) * 20)
        return {"score": score, "status": "CRITICAL", "color": "#f97316",
                "explanation": f"{int(x)} units — hours from stockout. Expedite reorder."}

    elif x <= reorder_level:
        # Linear interpolation 20→45 from stock 5 → reorder_level
        score = int(20 + ((x - 5) / max(reorder_level - 5, 1)) * 25)
        return {"score": score, "status": "LOW", "color": "#eab308",
                "explanation": f"{int(x)} units — at or below reorder point ({int(reorder_level)}). Order now."}

    elif x <= 20:
        score = int(45 + ((x - reorder_level) / max(20 - reorder_level, 1)) * 25)
        return {"score": score, "status": "WARNING", "color": "#84cc16",
                "explanation": f"{int(x)} units — approaching reorder point. Monitor closely."}

    elif x <= 50:
        score = int(70 + ((x - 20) / 30) * 18)
        return {"score": score, "status": "HEALTHY", "color": "#22c55e",
                "explanation": f"{int(x)} units — healthy stock level."}

    elif x <= OVERSTOCK_THRESHOLD:
        score = 100
        return {"score": 100, "status": "OPTIMAL", "color": "#06b6d4",
                "explanation": f"{int(x)} units — optimal range. No action needed."}

    else:
        # Overstock penalty: capital tied up, physical liabilities
        excess          = x - OVERSTOCK_THRESHOLD
        penalty         = int((excess / 10) * OVERSTOCK_PENALTY * 100)
        score           = max(50, 100 - penalty)   # floor at 50 — overstock is bad but not crisis
        return {"score": score, "status": "OVERSTOCK", "color": "#a855f7",
                "explanation": f"{int(x)} units — overstock. Holding cost penalty: {penalty} pts. "
                               f"Capital tied up, degradation/expiry risk."}


# ─────────────────────────────────────────────────────────────
# 2.  ROW-WISE MAP  →  HEALTH VECTOR h
# ─────────────────────────────────────────────────────────────

def compute_health_vector(inv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies H(x) row-wise to the Current_Stock column vector.

    From session notes:
      x = [x1, x2, ..., xn]  (current stock per SKU)
      h = [H(x1), H(x2), ..., H(xn)]  (health score per SKU)

    This is the "Row Wise Mapping" — H(x) applied directly to the
    physical memory block of the current stock column vector.

    Defensive Guard Wall:
      N = 0  → return empty DataFrame with safe defaults (halt math)
      N > 0  → run the full map operation

    Returns:
        DataFrame with added columns: Health_Score, Health_Status,
        Health_Color, Health_Explanation
    """
    # ── GUARD WALL: N = 0 check ───────────────────────────────
    if inv_df is None or len(inv_df) == 0:
        print("  ⚠️  Guard wall triggered: N=0. No inventory data. Halting math operations.")
        return pd.DataFrame(columns=["Product_ID","Health_Score","Health_Status",
                                     "Health_Color","Health_Explanation"])

    # ── N > 0: Run row-vector map ─────────────────────────────
    print(f"  Running H(x) row-wise map over {len(inv_df)} SKUs...")
    df = inv_df.copy()

    reorder_col = "Reorder_Level" if "Reorder_Level" in df.columns else None

    h_scores, h_status, h_colors, h_explain = [], [], [], []

    for _, row in df.iterrows():
        stock   = row.get("Current_Stock", 0)
        rop     = row.get("Reorder_Level", 10) if reorder_col else 10
        result  = H(stock, reorder_level=float(rop))
        h_scores.append(result["score"])
        h_status.append(result["status"])
        h_colors.append(result["color"])
        h_explain.append(result["explanation"])

    df["Health_Score"]       = h_scores
    df["Health_Status"]      = h_status
    df["Health_Color"]       = h_colors
    df["Health_Explanation"] = h_explain

    return df


# ─────────────────────────────────────────────────────────────
# 3.  AGGREGATE REDUCTION  μ = (1/N) Σ h_i
# ─────────────────────────────────────────────────────────────

def aggregate_wellness_index(health_df: pd.DataFrame) -> dict:
    """
    Column-wise arithmetic mean reduction across the health vector h.

    Formula: μ = (1/N) × Σ h_i  for i in 1..N

    This is the single macroscopic wellness score for the whole store.
    Displayed as the top KPI on the Inventory Health page.

    Returns:
        dict with wellness_score, interpretation, and breakdown counts
    """
    if health_df is None or len(health_df) == 0 or "Health_Score" not in health_df.columns:
        return {"wellness_score": 0, "interpretation": "No data", "N": 0}

    h   = health_df["Health_Score"].values
    N   = len(h)
    mu  = float(np.sum(h) / N)   # explicit Σ / N matching the formula

    # Interpretation bands
    if mu >= 88:   interp, color = "Store is Thriving",       "#22c55e"
    elif mu >= 70: interp, color = "Store is Healthy",        "#84cc16"
    elif mu >= 50: interp, color = "Store Needs Attention",   "#eab308"
    elif mu >= 30: interp, color = "Store is At Risk",        "#f97316"
    else:          interp, color = "Store is in Crisis",      "#ef4444"

    # Count by status
    status_counts = health_df["Health_Status"].value_counts().to_dict()

    return {
        "wellness_score":  round(mu, 1),
        "N":               N,
        "interpretation":  interp,
        "color":           color,
        "status_counts":   status_counts,
        "formula":         f"μ = (1/{N}) × Σ h_i = {round(mu,1)}",
    }


# ─────────────────────────────────────────────────────────────
# 4.  BOOLEAN MASKING MATRIX  M_i = {1 if CRISIS, 0 otherwise}
# ─────────────────────────────────────────────────────────────

def boolean_mask_critical(health_df: pd.DataFrame,
                           statuses: list = None) -> pd.DataFrame:
    """
    Applies a conditional logical criteria mask to pull critical items.

    From session notes:
      M_i = 1 if status_i == "CRISIS"
      M_i = 0 otherwise

    We extend this to a multi-status mask (CRISIS + CRITICAL + LOW)
    so the Priority Alert dispatch can surface all actionable items,
    not just the most extreme ones.

    This pattern is called Layout Presentation Separation:
    The backend computes the mask; the frontend just renders M == 1 rows.

    Args:
        health_df: DataFrame with Health_Status column
        statuses:  List of status strings to flag (default: CRISIS, CRITICAL, LOW)

    Returns:
        DataFrame with M column added, filtered to M == 1 rows only
    """
    if statuses is None:
        statuses = ["CRISIS", "CRITICAL", "LOW"]

    if health_df is None or len(health_df) == 0:
        return pd.DataFrame()

    df = health_df.copy()

    # Boolean mask — vectorised via isin (O(n), no Python loop)
    df["M"] = df["Health_Status"].isin(statuses).astype(int)

    critical_items = df[df["M"] == 1].copy()

    # Sort by severity: CRISIS first, then CRITICAL, then LOW
    severity_order = {"CRISIS": 0, "CRITICAL": 1, "LOW": 2,
                      "WARNING": 3, "HEALTHY": 4, "OPTIMAL": 5, "OVERSTOCK": 6}
    critical_items["_sort"] = critical_items["Health_Status"].map(severity_order).fillna(9)
    critical_items = critical_items.sort_values("_sort").drop(columns=["_sort"])

    return critical_items


# ─────────────────────────────────────────────────────────────
# FULL PIPELINE
# ─────────────────────────────────────────────────────────────

def run_inventory_health_pipeline(inv_df: pd.DataFrame) -> tuple:
    """
    Runs all three steps in sequence and returns all outputs.

    Returns: (health_df, wellness, critical_df)
    """
    print("\n🏥  Inventory Health Pipeline")
    print("=" * 45)

    # Guard wall
    if inv_df is None or len(inv_df) == 0:
        print("  Guard wall: N=0. Returning safe defaults.")
        empty = pd.DataFrame()
        return empty, {"wellness_score": 0, "interpretation": "No data", "N": 0}, empty

    # Step 1: Row-wise H(x) map
    health_df  = compute_health_vector(inv_df)

    # Step 2: Aggregate reduction μ
    wellness   = aggregate_wellness_index(health_df)
    print(f"  Store Wellness Index μ = {wellness['wellness_score']}/100  ({wellness['interpretation']})")
    print(f"  Formula: {wellness['formula']}")

    # Step 3: Boolean mask — CRISIS + CRITICAL + LOW items
    critical_df = boolean_mask_critical(health_df, statuses=["CRISIS","CRITICAL","LOW"])
    print(f"  Priority alerts (M=1): {len(critical_df)} SKUs flagged")
    print(f"  Status breakdown: {wellness['status_counts']}")

    return health_df, wellness, critical_df


# ─────────────────────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    inv_path = "data/raw/inventory.csv"
    if os.path.exists(inv_path):
        inv = pd.read_csv(inv_path)
    else:
        # Minimal demo dataset
        inv = pd.DataFrame({
            "Product_ID":    [1,2,3,4,5,6,7],
            "Product_Name":  ["Croissant","Sourdough","Birthday Cake","Latte","Baguette","Red Velvet","Cold Brew"],
            "Category":      ["Pastries","Breads","Cakes","Drinks","Breads","Cakes","Drinks"],
            "Current_Stock": [0, 3, 8, 15, 35, 75, 150],
            "Reorder_Level": [10,10,10,10,10,10,10],
            "Cost_Price":    [1.2,2.5,8.0,0.6,1.0,3.2,0.5],
            "Retail_Price":  [3.5,7.5,32.0,4.75,3.5,7.0,4.25],
        })

    health_df, wellness, critical_df = run_inventory_health_pipeline(inv)

    print("\n── H(x) Results per SKU ──")
    cols = ["Product_Name","Current_Stock","Health_Score","Health_Status"]
    available = [c for c in cols if c in health_df.columns]
    print(health_df[available].to_string(index=False))

    if len(critical_df) > 0:
        print("\n── Priority Alerts (Boolean Mask M=1) ──")
        alert_cols = [c for c in ["Product_Name","Current_Stock","Health_Score","Health_Status","Health_Explanation"] if c in critical_df.columns]
        print(critical_df[alert_cols].to_string(index=False))

    print("\n✅  Inventory health pipeline complete.\n")
