from __future__ import annotations

import hmac
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Path as PathParameter, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from src.storage import HealthStore, METRIC_NAME_PATTERN


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
RETENTION_DAYS = int(os.environ.get("RAW_RETENTION_DAYS", "30"))
DATA_ROOT = Path(os.environ.get("HEALTH_DATA_DIR", "/data"))
TIMEZONE = os.environ.get("HEALTH_TIMEZONE", "Europe/Madrid")
store = HealthStore(DATA_ROOT, TIMEZONE)

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
    result = store.ingest(body, payload, {key.lower(): value for key, value in request.headers.items()})
    store.prune_raw(RETENTION_DAYS)
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
    metric: str = PathParameter(pattern=METRIC_NAME_PATTERN),
    days: int = Query(90, ge=1, le=3650),
) -> dict[str, object]:
    authorize(request)
    return {"metric": metric, "days": days, "data": store.metric_summary(metric, days)}
