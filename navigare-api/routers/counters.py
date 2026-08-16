"""
Counters router — tracks signup and guest-mode usage.
"""

import os
import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

COUNTERS_FILE = os.environ.get("COUNTERS_FILE", "/app/counters.json")

DEFAULT_COUNTERS = {
    "email_signups": 0,
    "guest_sessions": 0,
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
    counters["total_users"] = counters.get("email_signups", 0) + counters.get("guest_sessions", 0)
    return counters


@router.post("/counters/email-signup")
def increment_email_signup():
    counters = load_counters()
    counters["email_signups"] = counters.get("email_signups", 0) + 1
    save_counters(counters)
    return {"email_signups": counters["email_signups"]}


@router.post("/counters/guest-session")
def increment_guest_session():
    counters = load_counters()
    counters["guest_sessions"] = counters.get("guest_sessions", 0) + 1
    save_counters(counters)
    return {"guest_sessions": counters["guest_sessions"]}
