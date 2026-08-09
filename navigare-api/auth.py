"""
Centralized authentication and security utilities for Navigare API.
"""

import os
import secrets
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=True)


async def rate_limiter(request: Request):
    """Simple in-memory rate limiter: 60 requests per minute per IP."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rl:{client_ip}"

    if not hasattr(rate_limiter, "_store"):
        rate_limiter._store = {}

    store = rate_limiter._store
    now = __import__("time").time()

    if key in store:
        count, window_start = store[key]
        if now - window_start < 60:
            if count >= 60:
                raise HTTPException(status_code=429, detail="Too many requests. Try again in a minute.")
            store[key] = (count + 1, window_start)
        else:
            store[key] = (1, now)
    else:
        store[key] = (1, now)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify bearer token using constant-time comparison.
    Raises 503 if APP_SECRET is not configured, 401 if token is invalid.
    """
    expected = os.environ.get("APP_SECRET")
    if not expected:
        raise HTTPException(status_code=503, detail="Server not configured — APP_SECRET missing")
    token = credentials.credentials
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token
