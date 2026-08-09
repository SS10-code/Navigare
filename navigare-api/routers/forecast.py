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
