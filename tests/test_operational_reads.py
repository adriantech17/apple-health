from __future__ import annotations

import hashlib
import importlib
import json
import sys
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.live_ingestion import OperationalLiveStore
from src.metric_contracts import METRIC_CONTRACTS
from src.operational_store import OperationalStore, VersionCandidate
from src.storage_schema import OperationalWriterLock, connect_operational, create_operational_database


USER_ID = "primary-user"
TOKEN = "test-token-with-at-least-32-characters"
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)
SOURCE = {"automation-name": "Default", "automation-id": "daily", "session-id": "synthetic"}


def create_runtime(tmp_path: Path, now: datetime = NOW) -> tuple[OperationalLiveStore, Path]:
    root = tmp_path / "candidate"
    root.mkdir(mode=0o700)
    database = create_operational_database(root, user_id=USER_ID)
    return OperationalLiveStore(database, user_id=USER_ID, clock=lambda: now), database


def body(name: str, unit: str, row: dict[str, object]) -> bytes:
    return json.dumps({"data": {"metrics": [{"name": name, "units": unit, "data": [row]}]}}).encode()


def test_current_reads_use_inclusive_madrid_dates_and_one_aligned_version(tmp_path: Path):
    runtime, _ = create_runtime(tmp_path)
    runtime.ingest(body("heart_rate", "bpm", {"Min": 45, "Avg": 60, "Max": 90, "date": "2026-10-25"}), SOURCE)
    runtime.ingest(body("heart_rate", "count/min", {"Min": 50, "Avg": 70, "Max": 100, "date": "2026-10-25"}), SOURCE)
    runtime.ingest(body("heart_rate", "bpm", {"Min": 40, "Avg": 55, "Max": 80, "date": "2026-10-24"}), SOURCE)
    result = runtime.metric_summary("heart_rate", 2)

    assert result == [
        {"date": "2026-10-24", "value": 55, "unit": "bpm", "samples": 1, "details": {"maximum": 80, "minimum": 40}},
        {"date": "2026-10-25", "value": 70, "unit": "bpm", "samples": 1, "details": {"maximum": 100, "minimum": 50}},
    ]


@pytest.mark.parametrize(
    "now,expected_today",
    (
        (datetime(2026, 3, 29, 22, 30, tzinfo=UTC), "2026-03-30"),
        (datetime(2026, 10, 25, 22, 30, tzinfo=UTC), "2026-10-25"),
    ),
)
def test_read_window_ends_on_madrid_today_across_dst(tmp_path: Path, now: datetime, expected_today: str):
    runtime, _ = create_runtime(tmp_path, now)
    runtime.ingest(body("step_count", "count", {"qty": 1, "date": expected_today}), SOURCE)

    assert runtime.metric_summary("step_count", 1) == [
        {"date": expected_today, "value": 1, "unit": "count", "samples": 1}
    ]


def test_tombstones_and_noncurrent_versions_are_omitted_and_empty_is_real(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    runtime.ingest(body("step_count", "count", {"qty": 9, "date": "2026-10-25"}), SOURCE)
    with OperationalWriterLock(database.parent) as writer, connect_operational(
        database, read_only=False, writer=writer
    ) as db:
        db.execute(
            "UPDATE metric_versions SET version_kind='absence',source_unit=NULL,canonical_unit=NULL,canonical_value=NULL,details_json=NULL"
        )

    assert runtime.metric_summary("step_count", 1) == []
    assert runtime.metric_summary("vo2_max", 30) == []


def test_status_preserves_meanings_and_ignores_replay_freshness(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    accepted = body("step_count", "count", {"qty": 3, "date": "2026-10-25"})
    runtime.ingest(accepted, SOURCE)
    runtime.ingest(accepted, SOURCE)
    OperationalStore(database, user_id=USER_ID).record_receipt(
        b'{"replay":"synthetic"}',
        receipt_id="replay-receipt",
        kind="replay",
        parser_version="1",
        contract_version="1",
        source_metadata={"automation_name": "Replay"},
        result="accepted",
        received_at=NOW + timedelta(hours=1),
        contract_valid=True,
        versions=(
            VersionCandidate("step_count", "2026-10-25", "value", "count", "count", "99", "{}", hashlib.sha256(b"replay").hexdigest(), "partial", "replay"),
        ),
    )

    status = runtime.status()

    assert status["imports"] == 2
    assert status["points"] == 1
    assert status["last_automation"] == "Default"
    assert status["last_import_at"].endswith("Z")


def load_candidate_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, timezone: str = "Europe/Madrid"
):
    tmp_path.chmod(0o700)
    datasets = tmp_path / "datasets"
    datasets.mkdir(mode=0o700)
    (datasets / "legacy").mkdir(mode=0o700)
    candidate = datasets / "candidate"
    candidate.mkdir(mode=0o700)
    database = create_operational_database(candidate, user_id=USER_ID, timezone=timezone)
    with OperationalWriterLock(candidate) as writer, connect_operational(
        database, read_only=False, writer=writer
    ) as db:
        db.execute("UPDATE dataset_state SET state='ready'")
    (tmp_path / "current").symlink_to("datasets/candidate")
    monkeypatch.setenv("HEALTH_API_TOKEN", TOKEN)
    monkeypatch.setenv("HEALTH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEALTH_DATA_LAYOUT", "pointer")
    monkeypatch.setenv("HEALTH_TIMEZONE", timezone)
    monkeypatch.setenv("HEALTH_USER_ID", USER_ID)
    sys.modules.pop("src.app", None)
    return importlib.import_module("src.app")


def test_candidate_read_routes_share_bearer_and_never_open_legacy_engines(monkeypatch, tmp_path: Path):
    module = load_candidate_app(monkeypatch, tmp_path)
    module.store._clock = lambda: NOW
    client = TestClient(module.app)
    headers = {"Authorization": f"Bearer {TOKEN}", **SOURCE}
    assert client.post(
        "/v1/ingest", content=body("step_count", "count", {"qty": 7, "date": "2026-10-25"}), headers=headers
    ).status_code == 200
    monkeypatch.setattr("src.storage.duckdb.connect", lambda: pytest.fail("DuckDB opened"))
    monkeypatch.setattr(Path, "glob", lambda *_: pytest.fail("legacy files scanned"))

    assert client.get("/v1/status").status_code == 401
    assert client.get("/v1/metrics/step_count").status_code == 401
    assert client.get("/v1/metrics/not-valid!", headers=headers).status_code == 422
    assert client.get("/v1/status", headers=headers).json()["points"] == 1
    assert client.get("/v1/metrics/step_count?days=1", headers=headers).json()["data"][0]["value"] == 7


def test_candidate_production_path_uses_configured_timezone_for_completeness_freshness_and_reads(
    monkeypatch, tmp_path: Path
):
    module = load_candidate_app(monkeypatch, tmp_path, timezone="America/New_York")
    module.store._clock = lambda: datetime(2026, 3, 29, 1, 0, tzinfo=UTC)
    client = TestClient(module.app)
    headers = {"Authorization": f"Bearer {TOKEN}", **SOURCE}

    assert client.post(
        "/v1/ingest",
        content=body("step_count", "count", {"qty": 6, "date": "2026-03-27"}),
        headers=headers,
    ).status_code == 200
    assert client.post(
        "/v1/ingest",
        content=body("step_count", "count", {"qty": 7, "date": "2026-03-28"}),
        headers=headers,
    ).status_code == 200

    with connect_operational(module.store.database) as db:
        assert db.execute(
            "SELECT local_date,completeness FROM metric_versions ORDER BY local_date"
        ).fetchall() == [("2026-03-27", "complete"), ("2026-03-28", "partial")]
        assert db.execute("SELECT latest_complete_local_date FROM live_freshness").fetchone() == (
            "2026-03-27",
        )
    assert client.get("/v1/metrics/step_count?days=1", headers=headers).json()["data"] == [
        {"date": "2026-03-28", "value": 7, "unit": "count", "samples": 1}
    ]


def test_five_year_twenty_five_metric_plan_and_timing_are_bounded(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    start = date(2021, 10, 26)
    dates = [start + timedelta(days=offset) for offset in range((date(2026, 10, 25) - start).days + 1)]
    receipt_id = "performance-receipt"
    with OperationalWriterLock(database.parent) as writer, connect_operational(
        database, read_only=False, writer=writer
    ) as db:
        db.execute("INSERT INTO imports VALUES ('performance-import',?,?,1,'2026-10-25T00:00:00Z')", (USER_ID, "a" * 64))
        db.execute(
            "INSERT INTO import_receipts (receipt_id,user_id,import_id,kind,parser_version,contract_version,source_metadata_json,result,received_at,committed_at) VALUES (?,?,'performance-import','live','1','1','{}','accepted','2026-10-25T00:00:00Z','2026-10-25T00:00:00Z')",
            (receipt_id, USER_ID),
        )
        db.execute("INSERT INTO authority_events (user_id,authority_sequence,live_receipt_id,live_receipt_kind,created_at) VALUES (?,1,?,'live','2026-10-25T00:00:00Z')", (USER_ID, receipt_id))
        rows = [
            (str(uuid.uuid4()), USER_ID, receipt_id, name, day.isoformat(), hashlib.sha256(f"{name}:{day}".encode()).hexdigest())
            for name in METRIC_CONTRACTS
            for day in dates
        ]
        db.executemany(
            "INSERT INTO metric_versions (version_id,user_id,receipt_id,metric,local_date,version_kind,source_unit,canonical_unit,canonical_value,details_json,context_fingerprint,completeness,validation_status,live_authority_sequence) VALUES (?,?,?, ?,?,'value','synthetic','synthetic','1','{}',?,'complete','valid',1)",
            rows,
        )
        db.executemany("INSERT INTO metric_current (user_id,metric,local_date,version_id) VALUES (?,?,?,?)", ((USER_ID, row[3], row[4], row[0]) for row in rows))
    with connect_operational(database) as db:
        plan = " ".join(row[3] for row in db.execute(
            "EXPLAIN QUERY PLAN SELECT v.canonical_value FROM metric_current c JOIN metric_versions v ON v.version_id=c.version_id WHERE c.user_id=? AND c.metric=? AND c.local_date BETWEEN ? AND ? ORDER BY c.local_date",
            (USER_ID, "step_count", start.isoformat(), "2026-10-25"),
        ))
    started = time.perf_counter()
    result = runtime.metric_summary("step_count", len(dates))
    elapsed = time.perf_counter() - started

    assert len(rows) == 25 * len(dates)
    assert "SEARCH c" in plan and "SEARCH v" in plan and "SCAN" not in plan
    assert len(result) == len(dates)
    assert elapsed < 2.0
