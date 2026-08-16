"""
Inventory Health API — POST /api/inventory
Accepts transaction rows, returns health scores, wellness index, and priority alerts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from inventory_health import run_inventory_health_pipeline
from auth import verify_token

router = APIRouter()


class InventoryRequest(BaseModel):
    rows: list[dict]


@router.post("/inventory")
def inventory_health(payload: InventoryRequest, token: str = Depends(verify_token)):
    """
    Run inventory health pipeline on uploaded inventory data.
    Returns health scores per SKU, aggregate wellness index, and critical alerts.
    """
    if not payload.rows:
        raise HTTPException(status_code=400, detail="No rows provided")

    df = pd.DataFrame(payload.rows)

    required = {"Product_ID", "Product_Name", "Current_Stock"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    if "Reorder_Level" not in df.columns:
        df["Reorder_Level"] = 10.0

    health_df, wellness, critical_df = run_inventory_health_pipeline(df)

    response = {
        "health": health_df.to_dict("records") if health_df is not None and len(health_df) > 0 else [],
        "wellness": wellness,
        "critical": critical_df.to_dict("records") if critical_df is not None and len(critical_df) > 0 else [],
    }

    return response
