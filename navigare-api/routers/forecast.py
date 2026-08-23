"""
Forecast API — POST /api/forecast
Accepts transaction rows, returns SMA, EMA, and Holt-Winters forecasts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import verify_token

router = APIRouter()


class ForecastRequest(BaseModel):
    rows: list[dict]
    forecast_days: int = 14
    ema_span: int = 7
    seasonal_period: int = 7


@router.get("/forecast")
def forecast_demo():
    dates = ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05", "2026-07-06", "2026-07-07"]
    actuals = [4200, 3800, 5100, 4600, 6200, 7800, 5500]
    return {
        "dates": dates,
        "actuals": actuals,
        "sma": [4200, 4000, 4367, 4567, 5167, 5867, 5500],
        "ema": [4200, 4100, 4433, 4575, 4962, 5738, 5619],
        "hw_ok": True,
        "hw_fitted": [4200, 3900, 4800, 4600, 5900, 7200, 5800],
        "hw_forecast": [
            {"date": "2026-07-08", "value": 6100},
            {"date": "2026-07-09", "value": 6300},
            {"date": "2026-07-10", "value": 5900},
            {"date": "2026-07-11", "value": 6200},
            {"date": "2026-07-12", "value": 6500},
        ],
        "hw_mae": 245.0,
        "sma_mae": 180.0,
        "ema_mae": 155.0,
    }


@router.get("/inventory")
def inventory_demo():
    return {
        "dates": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "actuals": [35, 8, 42, 12, 28],
    }


@router.get("/customers")
def customers_demo():
    return {
        "segments": [
            {"name": "Champions", "value": 45, "count": 18},
            {"name": "Loyal", "value": 25, "count": 15},
            {"name": "At Risk", "value": 15, "count": 7},
            {"name": "New", "value": 10, "count": 5},
        ],
    }


@router.post("/forecast")
def forecast(payload: ForecastRequest, token: str = Depends(verify_token)):
    if not payload.rows:
        raise HTTPException(status_code=400, detail="No rows provided")

    df = pd.DataFrame(payload.rows)
    required = {"Transaction_Date", "Line_Total_USD"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
    daily = df.groupby("Transaction_Date")["Line_Total_USD"].sum().resample("D").sum().fillna(0)

    if len(daily) < 3:
        raise HTTPException(status_code=400, detail="Not enough data points for forecasting (need at least 3 days)")

    sma = daily.rolling(min(7, len(daily)), min_periods=1).mean().tolist()
    ema = daily.ewm(span=payload.ema_span, adjust=False).mean().tolist()

    hw_ok = False
    hw_fitted = []
    hw_forecast = []
    try:
        hw = ExponentialSmoothing(
            daily, trend="add", seasonal="add",
            seasonal_periods=min(payload.seasonal_period, len(daily) // 2),
            initialization_method="estimated"
        ).fit(optimized=True)
        hw_fitted = hw.fittedvalues.tolist()
        hw_fc_idx = pd.date_range(daily.index[-1] + pd.Timedelta(days=1), periods=payload.forecast_days, freq="D")
        hw_forecast = [{"date": str(d.date()), "value": float(v)} for d, v in zip(hw_fc_idx, hw.forecast(payload.forecast_days))]
        hw_ok = True
    except Exception as e:
        pass

    dates = [str(d.date()) for d in daily.index]
    actuals = daily.tolist()

    return {
        "dates": dates,
        "actuals": actuals,
        "sma": sma,
        "ema": ema,
        "hw_ok": hw_ok,
        "hw_fitted": hw_fitted,
        "hw_forecast": hw_forecast,
        "hw_mae": float((daily - pd.Series(hw_fitted, index=daily.index)).abs().mean()) if hw_ok and hw_fitted else None,
        "sma_mae": float((daily - pd.Series(sma, index=daily.index)).abs().mean()) if sma else None,
        "ema_mae": float((daily - pd.Series(ema, index=daily.index)).abs().mean()) if ema else None,
    }
