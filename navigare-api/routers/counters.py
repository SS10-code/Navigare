"""
Counters router — tracks business clients and regular clients.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

COUNTERS_FILE = os.environ.get("COUNTERS_FILE", "/app/counters.json")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

DEFAULT_COUNTERS = {
    "business_clients": 0,
    "clients": 0,
}


def load_counters() -> dict:
    try:
        with open(COUNTERS_FILE, "r") as f:
            data = json.load(f)
            for key in DEFAULT_COUNTERS:
                if key not in data:
                    data[key] = DEFAULT_COUNTERS[key]
            return data
    except FileNotFoundError:
        return DEFAULT_COUNTERS.copy()


def save_counters(counters: dict) -> None:
    os.makedirs(os.path.dirname(COUNTERS_FILE), exist_ok=True)
    with open(COUNTERS_FILE, "w") as f:
        json.dump(counters, f, indent=2)


@router.get("/counters")
def get_counters():
    counters = load_counters()
    counters["total_clients"] = counters.get("business_clients", 0) + counters.get("clients", 0)
    return counters


@router.post("/counters/business-client")
def increment_business_client():
    counters = load_counters()
    counters["business_clients"] = counters.get("business_clients", 0) + 1
    save_counters(counters)
    return {"business_clients": counters["business_clients"]}


@router.post("/counters/client")
def increment_client():
    counters = load_counters()
    counters["clients"] = counters.get("clients", 0) + 1
    save_counters(counters)
    return {"clients": counters["clients"]}


@router.post("/counters/reset")
def reset_counters():
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=404, detail="Not found")
    token = os.environ.get("ADMIN_TOKEN", "")
    if not token:
        raise HTTPException(status_code=500, detail="Admin token not configured")
    save_counters(DEFAULT_COUNTERS.copy())
    return {"status": "reset"}
