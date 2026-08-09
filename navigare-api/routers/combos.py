"""
Combos API — POST /api/combos
Accepts transaction rows, returns market basket pairs (what sells together).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import pandas as pd
from itertools import combinations
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from business_metrics import compute_combo_pairs
from auth import verify_token

router = APIRouter()


class CombosRequest(BaseModel):
    rows: list[dict]
    min_support: float = 0.02
    top_n: int = 30


@router.post("/combos")
def combos(payload: CombosRequest, token: str = Depends(verify_token)):
    if not payload.rows:
        raise HTTPException(status_code=400, detail="No rows provided")

    df = pd.DataFrame(payload.rows)
    required = {"Transaction_ID", "Product_ID"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    combo_df = compute_combo_pairs(df, min_support=payload.min_support, top_n=payload.top_n)

    if combo_df is None or len(combo_df) == 0:
        return {"pairs": []}

    return {"pairs": combo_df.to_dict("records")}
