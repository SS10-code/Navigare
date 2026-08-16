"""
Track router for logging guest and authenticated user events to Supabase.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import httpx

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")


@router.post("/track")
async def track_event(request: Request):
    """
    Log guest or authenticated user events to Supabase.
    
    Accepts:
    - event: str - The event name
    - user_id: Optional[str] - The user ID if authenticated
    - properties: Optional[dict] - Additional event properties
    """
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON payload"}
        )

    event = data.get("event")
    user_id = data.get("user_id")
    properties = data.get("properties", {})

    if not event:
        return JSONResponse(
            status_code=400,
            content={"error": "Event name is required"}
        )

    payload = {
        "event": event,
        "user_id": user_id,
        "properties": properties,
        "timestamp": "now()",
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/events",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            return JSONResponse(content={"success": True})
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                status_code=e.response.status_code,
                content={"error": f"Failed to log event: {e.response.text}"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"}
            )