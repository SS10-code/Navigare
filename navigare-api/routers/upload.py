"""
Upload API — POST /api/upload/transactions and /api/upload/inventory
Accepts CSV files, returns basic stats.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import pandas as pd
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import verify_token

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_CONTENT_TYPES = {"text/csv", "application/vnd.ms-excel", "text/plain"}


async def validate_csv_file(file: UploadFile) -> bytes:
    """Validate file type and size, return contents."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content_type = file.content_type or ""
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    return contents


@router.post("/upload/transactions")
async def upload_transactions(file: UploadFile = File(...), token: str = Depends(verify_token)):
    contents = await validate_csv_file(file)
    try:
        df = pd.read_csv(io.BytesIO(contents), parse_dates=["Transaction_Date"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV format or missing Transaction_Date column")

    return {
        "status": "uploaded",
        "filename": os.path.basename(file.filename),
        "rows": len(df),
        "columns": df.columns.tolist(),
    }


@router.post("/upload/inventory")
async def upload_inventory(file: UploadFile = File(...), token: str = Depends(verify_token)):
    contents = await validate_csv_file(file)
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    return {
        "status": "uploaded",
        "filename": os.path.basename(file.filename),
        "rows": len(df),
        "columns": df.columns.tolist(),
    }
