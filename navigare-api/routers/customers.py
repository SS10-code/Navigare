"""
Customers API — POST /api/customers
Accepts transaction rows, returns RFM scores and segment counts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from business_metrics import compute_rfm
from auth import verify_token

router = APIRouter()


class CustomersRequest(BaseModel):
    rows: list[dict]


@router.post("/customers")
def customers(payload: CustomersRequest, token: str = Depends(verify_token)):
    if not payload.rows:
        raise HTTPException(status_code=400, detail="No rows provided")

    df = pd.DataFrame(payload.rows)
    required = {"Transaction_ID", "Transaction_Date", "Customer_ID", "Line_Total_USD"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
    rfm_df = compute_rfm(df)

    if rfm_df is None or len(rfm_df) == 0:
        return {"segments": {}, "customers": []}

    segments = rfm_df["Segment"].value_counts().to_dict() if "Segment" in rfm_df.columns else {}
    customers = rfm_df.to_dict("records")

    return {"segments": segments, "customers": customers}
