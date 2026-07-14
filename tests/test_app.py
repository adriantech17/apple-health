from __future__ import annotations

import importlib
import json
import sys
from datetime import UTC, datetime

from fastapi.testclient import TestClient


def load_app(monkeypatch, tmp_path):
    monkeypatch.setenv("HEALTH_API_TOKEN", "test-token-with-at-least-32-characters")
    monkeypatch.setenv("HEALTH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEALTH_TIMEZONE", "Europe/Madrid")
    sys.modules.pop("src.app", None)
    return importlib.import_module("src.app")


def test_health_endpoint_does_not_require_authentication(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)

    response = TestClient(module.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_endpoint_rejects_missing_token(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)

    response = TestClient(module.app).get("/v1/status")

    assert response.status_code == 401


def test_ingests_health_auto_export_payload(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    client = TestClient(module.app)
    headers = {"Authorization": f"Bearer {module.TOKEN}"}
    observed_at = datetime.now(UTC).strftime("%Y-%m-%d 12:00:00 +0000")
    payload = {
        "data": {
            "metrics": [
                {
                    "name": "step_count",
                    "units": "count",
                    "data": [{"qty": 4200, "date": observed_at}],
                }
            ]
        }
    }

    ingest = client.post(
        "/v1/ingest",
        content=json.dumps(payload),
        headers=headers,
    )
    metric = client.get("/v1/metrics/step_count?days=30", headers=headers)

    assert ingest.status_code == 200
    assert ingest.json()["inserted_points"] == 1
    assert metric.status_code == 200
    assert metric.json()["data"][0]["value"] == 4200


def test_rejects_invalid_metric_name(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    headers = {"Authorization": f"Bearer {module.TOKEN}"}

    response = TestClient(module.app).get("/v1/metrics/not-valid!", headers=headers)

    assert response.status_code == 422
