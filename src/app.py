from __future__ import annotations

import hmac
import json
import os
from pathlib import Path

from anyio import CancelScope
from fastapi import FastAPI, HTTPException, Path as PathParameter, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from src.maintenance import GateActive, MaintenanceGate, resolve_data_root
from src.storage import HealthStore


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


TOKEN = read_secret("HEALTH_API_TOKEN")
MAX_BODY = int(os.environ.get("MAX_BODY_MB", "128")) * 1024 * 1024
CONFIGURED_DATA_ROOT = Path(os.environ.get("HEALTH_DATA_DIR", "/data"))
DATA_LAYOUT = os.environ.get("HEALTH_DATA_LAYOUT", "direct")
TIMEZONE = os.environ.get("HEALTH_TIMEZONE", "Europe/Madrid")

if DATA_LAYOUT not in {"direct", "pointer"}:
    raise RuntimeError("HEALTH_DATA_LAYOUT must be 'direct' or 'pointer'")
DATA_ROOT, GATE_ROOT = resolve_data_root(CONFIGURED_DATA_ROOT, pointer_layout=DATA_LAYOUT == "pointer")
PRIVATE_UMASK_PREVIOUS = os.umask(0o077) if DATA_LAYOUT == "pointer" else None

if "RAW_RETENTION_DAYS" in os.environ:
    raise RuntimeError("RAW_RETENTION_DAYS is no longer supported; raw payloads are retained")

store = HealthStore(DATA_ROOT, TIMEZONE)
gate = MaintenanceGate(GATE_ROOT)

if len(TOKEN) < 32:
    raise RuntimeError("HEALTH_API_TOKEN must contain at least 32 characters")

app = FastAPI(title="Private Apple Health Ingestion", docs_url=None, redoc_url=None, openapi_url=None)
origins = [item.strip() for item in os.environ.get("DASHBOARD_ORIGINS", "").split(",") if item.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["Authorization"])


def authorize(request: Request) -> None:
    supplied = request.headers.get("authorization", "")
    expected = f"Bearer {TOKEN}"
    if not TOKEN or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ingest")
async def ingest(request: Request) -> dict[str, object]:
    authorize(request)
    try:
        admission = gate.admit()
        await run_in_threadpool(admission.__enter__)
    except GateActive as error:
        raise HTTPException(status_code=503, detail="Ingestion temporarily unavailable", headers={"Retry-After": "60"}) from error
    try:
        content_length = int(request.headers.get("content-length", "0") or 0)
        if content_length > MAX_BODY:
            raise HTTPException(status_code=413, detail="Payload too large")
        body = await request.body()
        if len(body) > MAX_BODY:
            raise HTTPException(status_code=413, detail="Payload too large")
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise HTTPException(status_code=400, detail="Invalid JSON") from error
        container = payload.get("data", payload) if isinstance(payload, dict) else {}
        if not isinstance(container, dict) or not isinstance(container.get("metrics"), list):
            raise HTTPException(status_code=422, detail="Expected Health Auto Export JSON v2 with data.metrics")
        headers = {key.lower(): value for key, value in request.headers.items()}
        result = await run_in_threadpool(store.ingest, body, payload, headers)
    finally:
        with CancelScope(shield=True):
            await run_in_threadpool(admission.__exit__, None, None, None)
    return {
        "import_id": result.import_id,
        "duplicate_request": result.duplicate_request,
        "received_points": result.received_points,
        "inserted_points": result.inserted_points,
        "payload_sha256": result.payload_sha256,
    }


@app.get("/v1/status")
def status(request: Request) -> dict[str, object]:
    authorize(request)
    return store.status()


@app.get("/v1/metrics/{metric}")
def metric(
    request: Request,
    metric: str = PathParameter(pattern="^[a-z0-9_]+$"),
    days: int = Query(90, ge=1, le=3650),
) -> dict[str, object]:
    authorize(request)
    return {"metric": metric, "days": days, "data": store.metric_summary(metric, days)}
