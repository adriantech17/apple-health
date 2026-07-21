from __future__ import annotations

import fcntl
import importlib
import json
import os
import sys
from datetime import UTC, datetime

import anyio
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request


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
    assert set(ingest.json()) == {"import_id", "duplicate_request", "received_points", "inserted_points", "payload_sha256"}
    assert ingest.json()["inserted_points"] == 1
    assert metric.status_code == 200
    assert metric.json()["data"][0]["value"] == 4200


def test_ingest_does_not_prune_existing_raw_archives(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    old_archive = module.store.raw_dir / "synthetic-old.json.gz"
    old_archive.write_bytes(b"synthetic")
    old_timestamp = datetime.now(UTC).timestamp() - 31 * 86400
    os.utime(old_archive, (old_timestamp, old_timestamp))
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

    response = TestClient(module.app).post(
        "/v1/ingest",
        content=json.dumps(payload),
        headers={"Authorization": f"Bearer {module.TOKEN}"},
    )

    assert response.status_code == 200
    assert old_archive.exists()


def test_rejects_removed_raw_retention_setting(monkeypatch, tmp_path):
    monkeypatch.setenv("RAW_RETENTION_DAYS", "30")

    with pytest.raises(RuntimeError, match="RAW_RETENTION_DAYS is no longer supported"):
        load_app(monkeypatch, tmp_path)


def test_rejects_invalid_metric_name(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    headers = {"Authorization": f"Bearer {module.TOKEN}"}

    response = TestClient(module.app).get("/v1/metrics/not-valid!", headers=headers)

    assert response.status_code == 422


def test_unauthorized_ingest_does_not_check_maintenance(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    monkeypatch.setattr(module.gate, "admit", lambda: pytest.fail("gate checked"))

    response = TestClient(module.app).post("/v1/ingest", content=b"not-json")

    assert response.status_code == 401


def test_active_maintenance_rejects_before_body_and_keeps_reads(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    client = TestClient(module.app)
    headers = {"Authorization": f"Bearer {module.TOKEN}"}
    module.gate.activate()

    ingest = client.post("/v1/ingest", content=b"not-json", headers=headers)
    health = client.get("/health")
    status = client.get("/v1/status", headers=headers)
    metric = client.get("/v1/metrics/step_count", headers=headers)

    assert ingest.status_code == 503
    assert ingest.headers["retry-after"] == "60"
    assert health.status_code == 200
    assert status.status_code == 200
    assert metric.status_code == 200


def test_pointer_layout_starts_on_private_legacy_dataset(monkeypatch, tmp_path):
    tmp_path.chmod(0o700)
    datasets = tmp_path / "datasets"
    datasets.mkdir(mode=0o700)
    legacy = datasets / "legacy"
    legacy.mkdir(mode=0o700)
    (tmp_path / "current").symlink_to("datasets/legacy")
    monkeypatch.setenv("HEALTH_DATA_LAYOUT", "pointer")

    module = load_app(monkeypatch, tmp_path)
    os.umask(module.PRIVATE_UMASK_PREVIOUS)

    assert module.store.root == legacy
    assert module.gate.directory == tmp_path / "maintenance"
    assert module.store.raw_dir.stat().st_mode & 0o777 == 0o700
    assert module.store.db_path.stat().st_mode & 0o777 == 0o600


def test_ingest_dispatches_gate_and_storage_to_threadpool(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    dispatched: list[str] = []
    async def fake_threadpool(function, *args):
        dispatched.append(function.__name__)
        return function(*args)
    monkeypatch.setattr(module, "run_in_threadpool", fake_threadpool, raising=False)

    response = TestClient(module.app).post(
        "/v1/ingest",
        json={"data": {"metrics": []}},
        headers={"Authorization": f"Bearer {module.TOKEN}"},
    )

    assert response.status_code == 200
    assert dispatched == ["__enter__", "ingest", "__exit__"]


def test_unauthorized_ingest_does_not_receive_body(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    received = False
    async def receive():
        nonlocal received
        received = True
        return {"type": "http.request", "body": b"synthetic"}
    request = Request({"type": "http", "method": "POST", "path": "/v1/ingest", "headers": []}, receive)

    with pytest.raises(module.HTTPException) as captured:
        anyio.run(module.ingest, request)

    assert captured.value.status_code == 401
    assert not received


def test_busy_maintenance_lock_returns_retry_guidance(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    descriptor, directory = module.gate._open_lock()
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    try:
        response = TestClient(module.app).post(
            "/v1/ingest",
            content=b"not-json",
            headers={"Authorization": f"Bearer {module.TOKEN}"},
        )
    finally:
        os.close(descriptor)
        os.close(directory)
    assert response.status_code == 503
    assert response.headers["retry-after"] == "60"


def test_storage_error_releases_admission_lock(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    monkeypatch.setattr(module.store, "ingest", lambda *args: (_ for _ in ()).throw(RuntimeError("synthetic")))

    with pytest.raises(RuntimeError, match="synthetic"):
        TestClient(module.app).post(
            "/v1/ingest",
            json={"data": {"metrics": []}},
            headers={"Authorization": f"Bearer {module.TOKEN}"},
        )
    with module.gate.drain():
        pass


def test_cancelled_body_read_releases_admission_lock(monkeypatch, tmp_path):
    module = load_app(monkeypatch, tmp_path)
    headers = [(b"authorization", f"Bearer {module.TOKEN}".encode())]
    async def receive():
        await anyio.sleep_forever()
    request = Request({"type": "http", "method": "POST", "path": "/v1/ingest", "headers": headers}, receive)
    async def cancel_ingest():
        with anyio.move_on_after(0.01) as scope:
            await module.ingest(request)
        assert scope.cancel_called

    anyio.run(cancel_ingest)
    with module.gate.drain():
        pass
