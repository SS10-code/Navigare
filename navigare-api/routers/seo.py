"""
SEO API — POST /api/seo
Accepts body text and keywords, returns SEO audit report.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from seo_engine import analyse_text
from auth import verify_token

router = APIRouter()


class SEORequest(BaseModel):
    body_text: str
    keywords: list[str]
    remove_stopwords: bool = False


@router.post("/seo")
def seo(payload: SEORequest, token: str = Depends(verify_token)):
    if not payload.body_text.strip():
        raise HTTPException(status_code=400, detail="Body text is required")
    if not payload.keywords:
        raise HTTPException(status_code=400, detail="At least one keyword is required")

    report = analyse_text(payload.body_text, payload.keywords, remove_stopwords=payload.remove_stopwords)

    if "error" in report:
        raise HTTPException(status_code=400, detail=report["error"])

    return report
