"""
Navigare Analytics API — FastAPI backend for Render deployment
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from routers import inventory, customers, forecast, combos, seo, digest, upload, track
from auth import verify_token, rate_limiter

app = FastAPI(
    title="Navigare Analytics API",
    description="Retail analytics endpoints for local business owners",
    version="1.0.0",
)

security = HTTPBearer(auto_error=True)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject request bodies larger than 10MB to prevent abuse."""
    max_body = 10 * 1024 * 1024
    if request.method in ("POST", "PUT"):
        cl = request.headers.get("content-length")
        if cl and int(cl) > max_body:
            return JSONResponse(status_code=413, content={"detail": "Request too large (max 10MB)"})
    return await call_next(request)


app.include_router(inventory.router, prefix="/api", tags=["inventory"], dependencies=[Depends(rate_limiter)])
app.include_router(customers.router, prefix="/api", tags=["customers"], dependencies=[Depends(rate_limiter)])
app.include_router(forecast.router, prefix="/api", tags=["forecast"], dependencies=[Depends(rate_limiter)])
app.include_router(combos.router, prefix="/api", tags=["combos"], dependencies=[Depends(rate_limiter)])
app.include_router(seo.router, prefix="/api", tags=["seo"], dependencies=[Depends(rate_limiter)])
app.include_router(digest.router, prefix="/api", tags=["digest"], dependencies=[Depends(rate_limiter)])
app.include_router(upload.router, prefix="/api", tags=["upload"], dependencies=[Depends(rate_limiter)])
app.include_router(track.router, prefix="/api", tags=["track"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "navigare-api"}


@app.post("/api/verify-token")
def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify a bearer token against the shared API secret."""
    token = verify_token(credentials)
    return {"valid": True}
