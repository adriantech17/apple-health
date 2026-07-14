from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import os
import re
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import httpx
from fastapi import Cookie, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse


def read_secret(name: str) -> str:
    """Read a Docker secret, with an environment fallback for local tests."""
    secret_file = os.environ.get(f"{name}_FILE")
    if secret_file:
        try:
            value = Path(secret_file).read_text(encoding="utf-8").strip()
        except OSError as error:
            raise RuntimeError(f"Unable to read {name}_FILE") from error
        if not value:
            raise RuntimeError(f"{name}_FILE is empty")
        return value
    return os.environ.get(name, "")


API_BASE = os.environ.get("HEALTH_API_BASE_URL", "http://health-ingestion:8787").rstrip("/")
API_TOKEN = read_secret("HEALTH_API_TOKEN")
DASHBOARD_PASSWORD = read_secret("DASHBOARD_PASSWORD")
SESSION_SECRET = read_secret("DASHBOARD_SESSION_SECRET")
COOKIE_SECURE = os.environ.get("DASHBOARD_COOKIE_SECURE", "true").lower() == "true"
SESSION_SECONDS = int(os.environ.get("DASHBOARD_SESSION_HOURS", "12")) * 3600
MAX_ACTIVE_SESSIONS = 64
MAX_LOGIN_CLIENTS = 1024
STATIC_DIR = Path("/app/static")
COOKIE_NAME = "healthscope_session"
METRIC_PATTERN = re.compile(r"^[a-z0-9_]+$")

if len(API_TOKEN) < 32:
    raise RuntimeError("HEALTH_API_TOKEN must contain at least 32 characters")
if len(DASHBOARD_PASSWORD) < 12:
    raise RuntimeError("DASHBOARD_PASSWORD must contain at least 12 characters")
if len(SESSION_SECRET) < 32:
    raise RuntimeError("DASHBOARD_SESSION_SECRET must contain at least 32 characters")

app = FastAPI(title="HealthScope Dashboard", docs_url=None, redoc_url=None, openapi_url=None)
failed_logins: dict[str, deque[float]] = defaultdict(deque)
active_sessions: dict[str, int] = {}
login_lock = asyncio.Lock()


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_session() -> str:
    expiry = int(time.time()) + SESSION_SECONDS
    payload = f"{expiry}.{secrets.token_urlsafe(18)}"
    signature = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    nonce = payload.split(".", 1)[1]
    _prune_active_sessions()
    if len(active_sessions) >= MAX_ACTIVE_SESSIONS:
        oldest = min(active_sessions, key=active_sessions.get)
        active_sessions.pop(oldest, None)
    active_sessions[nonce] = expiry
    return f"{payload}.{_b64(signature)}"


def _session_parts(token: str | None) -> tuple[int, str] | None:
    if not token:
        return None
    try:
        expiry_raw, nonce, supplied = token.split(".", 2)
        expiry = int(expiry_raw)
        if expiry < int(time.time()) or not nonce:
            return None
        payload = f"{expiry_raw}.{nonce}"
        expected = _b64(hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).digest())
        return (expiry, nonce) if hmac.compare_digest(supplied, expected) else None
    except (ValueError, TypeError):
        return None


def _prune_active_sessions() -> None:
    now = int(time.time())
    for nonce, expiry in list(active_sessions.items()):
        if expiry < now:
            active_sessions.pop(nonce, None)


def valid_session(token: str | None) -> bool:
    parts = _session_parts(token)
    if parts is None:
        return False
    expiry, nonce = parts
    _prune_active_sessions()
    return active_sessions.get(nonce) == expiry


def revoke_session(token: str | None) -> None:
    parts = _session_parts(token)
    if parts is None:
        return
    _, nonce = parts
    active_sessions.pop(nonce, None)


def require_session(session: str | None) -> None:
    if not valid_session(session):
        raise HTTPException(status_code=401, detail="Authentication required")


def check_rate_limit(client: str) -> None:
    now = time.time()
    for known_client, known_attempts in list(failed_logins.items()):
        if not known_attempts or known_attempts[-1] < now - 300:
            failed_logins.pop(known_client, None)
    if client not in failed_logins and len(failed_logins) >= MAX_LOGIN_CLIENTS:
        oldest = min(failed_logins, key=lambda item: failed_logins[item][-1])
        failed_logins.pop(oldest, None)
    attempts = failed_logins[client]
    while attempts and attempts[0] < now - 300:
        attempts.popleft()
    if len(attempts) >= 5:
        raise HTTPException(status_code=429, detail="Too many attempts; try again later")


async def authenticate(client: str, password: str | None) -> bool:
    async with login_lock:
        check_rate_limit(client)
        try:
            valid = isinstance(password, str) and hmac.compare_digest(
                password.encode("utf-8"), DASHBOARD_PASSWORD.encode("utf-8")
            )
        except UnicodeEncodeError:
            valid = False
        if not valid:
            failed_logins[client].append(time.time())
            return False
        failed_logins.pop(client, None)
        return True


async def ingestion_get(path: str, params: dict[str, Any] | None = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{API_BASE}{path}",
                params=params,
                headers={"Authorization": f"Bearer {API_TOKEN}"},
            )
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(status_code=502, detail="Health data service unavailable") from error


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/auth/status")
def auth_status(healthscope_session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict[str, bool]:
    return {"authenticated": valid_session(healthscope_session)}


@app.post("/api/auth/login")
async def login(request: Request, response: Response) -> dict[str, bool]:
    client = request.client.host if request.client else "unknown"
    try:
        body = await request.json()
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid request") from error
    password = body.get("password") if isinstance(body, dict) else None
    if not await authenticate(client, password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(
        COOKIE_NAME,
        create_session(),
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {"authenticated": True}


@app.post("/api/auth/logout")
def logout(
    response: Response,
    healthscope_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> dict[str, bool]:
    revoke_session(healthscope_session)
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )
    return {"authenticated": False}


@app.get("/api/status")
async def status(healthscope_session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> Any:
    require_session(healthscope_session)
    return await ingestion_get("/v1/status")


@app.get("/api/metrics/{metric}")
async def metric(
    metric: str,
    days: int = Query(90, ge=1, le=3650),
    healthscope_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Any:
    require_session(healthscope_session)
    if not METRIC_PATTERN.fullmatch(metric):
        raise HTTPException(status_code=400, detail="Invalid metric")
    return await ingestion_get(f"/v1/metrics/{metric}", {"days": days})


@app.get("/{path:path}")
def static_app(path: str) -> FileResponse:
    candidate = STATIC_DIR / path
    if path and candidate.is_file() and STATIC_DIR in candidate.resolve().parents:
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")
