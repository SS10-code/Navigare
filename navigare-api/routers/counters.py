"""
Counters router — tracks business clients and regular clients in Supabase.
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

COUNTERS_ID = 1


async def init_counters():
    """Ensure the counters row exists in Supabase."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/counters?id=eq.{COUNTERS_ID}",
            headers=HEADERS,
        )
        if resp.status_code == 200 and not resp.json():
            await client.post(
                f"{SUPABASE_URL}/rest/v1/counters",
                headers=HEADERS,
                json={"id": COUNTERS_ID, "business_clients": 0, "clients": 0},
            )


async def get_counters() -> dict:
    """Fetch counters from Supabase."""
    await init_counters()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/counters?id=eq.{COUNTERS_ID}",
            headers=HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else {"business_clients": 0, "clients": 0}


async def update_counters(business_clients: int = None, clients: int = None) -> dict:
    """Update counters in Supabase."""
    await init_counters()
    patch = {}
    if business_clients is not None:
        patch["business_clients"] = business_clients
    if clients is not None:
        patch["clients"] = clients

    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{SUPABASE_URL}/rest/v1/counters?id=eq.{COUNTERS_ID}",
            headers=HEADERS,
            json=patch,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else {"business_clients": 0, "clients": 0}


@router.get("/counters")
async def get_counters_endpoint():
    counters = await get_counters()
    return {
        "business_clients": counters.get("business_clients", 0),
        "clients": counters.get("clients", 0),
        "total_clients": counters.get("business_clients", 0) + counters.get("clients", 0),
    }


@router.post("/counters/business-client")
async def increment_business_client():
    counters = await get_counters()
    new_val = counters.get("business_clients", 0) + 1
    await update_counters(business_clients=new_val)
    return {"business_clients": new_val}


@router.post("/counters/client")
async def increment_client():
    counters = await get_counters()
    new_val = counters.get("clients", 0) + 1
    await update_counters(clients=new_val)
    return {"clients": new_val}


@router.post("/counters/reset")
async def reset_counters():
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=404, detail="Not found")
    await update_counters(business_clients=0, clients=0)
    return {"status": "reset"}