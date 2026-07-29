from __future__ import annotations

import importlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import anyio
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

import src.live_ingestion as live_ingestion
from src.live_ingestion import LiveIngestError, OperationalLiveStore
from src.storage_schema import OperationalWriterLock, connect_operational, create_operational_database


TOKEN = "test-token-with-at-least-32-characters"
USER_ID = "primary-user"
NOW = datetime(2026, 3, 29, 10, 0, tzinfo=UTC)
SOURCE = {"automation-name": "Default", "automation-id": "daily", "session-id": "synthetic"}


def payload(*metrics: dict[str, object]) -> bytes:
    return json.dumps({"data": {"metrics": list(metrics)}}, separators=(",", ":")).encode()


def metric(name: str, unit: str, *rows: dict[str, object]) -> dict[str, object]:
    return {"name": name, "units": unit, "data": list(rows)}


def create_runtime(tmp_path: Path, *, now: datetime = NOW, fault=None) -> tuple[OperationalLiveStore, Path]:
    root = tmp_path / "candidate"
    root.mkdir(mode=0o700)
    database = create_operational_database(root, user_id=USER_ID)
    return OperationalLiveStore(database, user_id=USER_ID, clock=lambda: now, fault=fault), database


def receipt_rows(database: Path) -> list[tuple[str, str]]:
    with connect_operational(database) as db:
        return db.execute("SELECT result, source_metadata_json FROM import_receipts ORDER BY rowid").fetchall()


def test_live_contract_preserves_success_shape_duplicate_context_and_madrid_completeness(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    body = payload(
        metric("step_count", "count", {"qty": 1200, "date": "2026-03-29"}),
        metric("resting_heart_rate", "bpm", {"qty": 58, "date": "2026-03-28 23:30:00 +0100"}),
    )

    first = runtime.ingest(body, SOURCE)
    duplicate = runtime.ingest(body, SOURCE)

    assert first.duplicate_request is False
    assert (first.received_points, first.inserted_points) == (2, 2)
    assert duplicate.duplicate_request is True
    assert duplicate.inserted_points == 0
    assert first.payload_sha256 == duplicate.payload_sha256
    with connect_operational(database) as db:
        assert db.execute(
            "SELECT metric,local_date,completeness FROM metric_versions ORDER BY metric"
        ).fetchall() == [
            ("resting_heart_rate", "2026-03-28", "complete"),
            ("step_count", "2026-03-29", "partial"),
        ]
        assert db.execute("SELECT COUNT(*) FROM imports").fetchone() == (1,)
        assert db.execute("SELECT COUNT(*) FROM import_receipts").fetchone() == (2,)
        assert db.execute("SELECT COUNT(*) FROM authority_events").fetchone() == (1,)


def test_unknown_closure_degraded_siblings_and_all_invalid_are_distinct(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    unknown_source = {"automation-name": "Default"}
    unknown = payload(metric("step_count", "count", {"qty": 10, "date": "2026-03-28"}))
    degraded = payload(
        metric("step_count", "count", {"qty": 20, "date": "2026-03-29"}),
        metric("heart_rate", "bpm", {"Min": 90, "Avg": 70, "Max": 80, "date": "2026-03-29"}),
    )
    invalid = payload(metric("step_count", "private-unit", {"qty": 999, "date": "2026-03-29"}))

    assert runtime.ingest(unknown, unknown_source).inserted_points == 1
    assert runtime.ingest(degraded, SOURCE).inserted_points == 1
    with pytest.raises(LiveIngestError) as rejected:
        runtime.ingest(invalid, SOURCE)

    assert (rejected.value.status_code, rejected.value.detail) == (422, "Invalid daily metrics")
    assert receipt_rows(database)[0][0] == "accepted"
    assert [row[0] for row in receipt_rows(database)] == ["accepted", "degraded", "rejected"]
    with connect_operational(database) as db:
        assert db.execute(
            "SELECT completeness FROM metric_versions WHERE local_date='2026-03-28'"
        ).fetchone() == ("unknown",)
        assert db.execute("SELECT code,metric FROM receipt_errors ORDER BY rowid").fetchall() == [
            ("invalid_details", "heart_rate"),
            ("unknown_unit", "step_count"),
        ]
        assert db.execute("SELECT COUNT(*) FROM receipt_artifacts").fetchone() == (3,)


def test_conflicting_daily_rows_are_not_clean_or_authoritative(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    conflicting = payload(metric("step_count", "count", {"qty": 1, "date": "2026-03-29"}, {"qty": 2, "date": "2026-03-29"}))

    with pytest.raises(LiveIngestError) as error:
        runtime.ingest(conflicting, SOURCE)

    assert error.value.status_code == 422
    with connect_operational(database) as db:
        assert db.execute("SELECT result FROM import_receipts").fetchone() == ("rejected",)
        assert db.execute("SELECT COUNT(*) FROM metric_versions").fetchone() == (0,)
        assert db.execute("SELECT code FROM receipt_errors").fetchall() == [("unresolved_conflict",)]


@pytest.mark.parametrize(
    "now,row_date,expected_date",
    (
        (datetime(2026, 3, 29, 1, 30, tzinfo=UTC), "2026-03-29 03:30:00 +0200", "2026-03-29"),
        (datetime(2026, 10, 25, 1, 30, tzinfo=UTC), "2026-10-25 02:30:00 +0100", "2026-10-25"),
    ),
)
def test_live_window_uses_offset_aware_madrid_dst_dates(tmp_path: Path, now: datetime, row_date: str, expected_date: str):
    runtime, database = create_runtime(tmp_path, now=now)

    runtime.ingest(payload(metric("step_count", "count", {"qty": 1, "date": row_date})), SOURCE)

    with connect_operational(database) as db:
        assert db.execute("SELECT local_date FROM metric_versions").fetchone() == (expected_date,)


@pytest.mark.parametrize("body,status", [(b"not-json", 400), (payload(), 422)])
def test_malformed_and_contract_invalid_requests_record_private_rejections_without_raw(
    tmp_path: Path, body: bytes, status: int
):
    runtime, database = create_runtime(tmp_path)

    with pytest.raises(LiveIngestError) as error:
        runtime.ingest(body, SOURCE if status == 400 else {"automation-name": "Other"})

    assert error.value.status_code == status
    assert str(error.value) in {"Invalid JSON", "Invalid live export contract"}
    with connect_operational(database) as db:
        assert db.execute("SELECT COUNT(*) FROM imports").fetchone() == (1,)
        assert db.execute("SELECT result FROM import_receipts").fetchone() == ("rejected",)
        assert db.execute("SELECT COUNT(*) FROM artifacts").fetchone() == (0,)


def test_four_freshness_dimensions_advance_independently_and_close_rollback(tmp_path: Path):
    runtime, database = create_runtime(tmp_path)
    with OperationalWriterLock(database.parent) as writer, connect_operational(
        database, read_only=False, writer=writer
    ) as db:
        db.execute("UPDATE dataset_state SET cutover_phase='accepted'")
    bodies = (
        b"not-json",
        payload(metric("step_count", "count", {"qty": 1, "date": "2026-03-29"}), metric("bad", "x", {"qty": 1, "date": "2026-03-29"})),
        payload(metric("step_count", "count", {"qty": 2, "date": "2026-03-28"})),
    )
    snapshots = []
    for body in bodies:
        try:
            runtime.ingest(body, SOURCE)
        except LiveIngestError:
            pass
        with connect_operational(database) as db:
            snapshots.append(db.execute(
                "SELECT latest_authenticated_receipt_id,latest_committed_receipt_id,latest_clean_receipt_id,latest_complete_local_date FROM live_freshness"
            ).fetchone())

    with connect_operational(database) as db:
        assert snapshots[0][0] and snapshots[0][1:] == (None, None, None)
        assert snapshots[1][0] == snapshots[1][1] and snapshots[1][2:] == (None, None)
        assert snapshots[2][0] == snapshots[2][1] == snapshots[2][2]
        assert snapshots[2][3] == "2026-03-28"
        assert db.execute("SELECT first_post_cutover_live_receipt_id FROM dataset_state").fetchone()[0]


@pytest.mark.parametrize("outcome", ("rejected", "degraded", "duplicate"))
def test_receipt_crash_rolls_back_freshness_and_rollback_closure(tmp_path: Path, outcome: str):
    runtime, database = create_runtime(tmp_path)
    good = payload(metric("step_count", "count", {"qty": 1, "date": "2026-03-29"}))
    if outcome == "duplicate":
        runtime.ingest(good, SOURCE)
    baseline = receipt_rows(database)

    def fault(point: str) -> None:
        if point == "after_freshness":
            raise RuntimeError("synthetic crash")

    crashing = OperationalLiveStore(database, user_id=USER_ID, clock=lambda: NOW, fault=fault)
    body = b"not-json" if outcome == "rejected" else (
        good if outcome == "duplicate" else payload(metric("step_count", "count", {"qty": 2, "date": "2026-03-29"}), metric("bad", "x", {"qty": 1, "date": "2026-03-29"}))
    )
    with pytest.raises(RuntimeError, match="synthetic crash"):
        crashing.ingest(body, SOURCE)

    assert receipt_rows(database) == baseline


def build_pointer_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, state: str = "ready"):
    tmp_path.chmod(0o700)
    datasets = tmp_path / "datasets"
    datasets.mkdir(mode=0o700)
    legacy = datasets / "legacy"
    legacy.mkdir(mode=0o700)
    candidate = datasets / "candidate"
    candidate.mkdir(mode=0o700)
    database = create_operational_database(candidate, user_id=USER_ID)
    with OperationalWriterLock(candidate) as writer, connect_operational(
        database, read_only=False, writer=writer
    ) as db:
        db.execute("UPDATE dataset_state SET state=?", (state,))
    (tmp_path / "current").symlink_to("datasets/candidate")
    monkeypatch.setenv("HEALTH_API_TOKEN", TOKEN)
    monkeypatch.setenv("HEALTH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HEALTH_DATA_LAYOUT", "pointer")
    monkeypatch.setenv("HEALTH_USER_ID", USER_ID)
    sys.modules.pop("src.app", None)
    return importlib.import_module("src.app"), legacy, database


def test_verified_candidate_route_preserves_five_fields_without_legacy_dual_write(monkeypatch, tmp_path: Path):
    module, legacy, database = build_pointer_app(monkeypatch, tmp_path)
    module.store._clock = lambda: NOW
    response = TestClient(module.app).post(
        "/v1/ingest",
        content=payload(metric("step_count", "count", {"qty": 42, "date": "2026-03-29"})),
        headers={"Authorization": f"Bearer {TOKEN}", **SOURCE},
    )

    assert response.status_code == 200
    assert set(response.json()) == {"import_id", "duplicate_request", "received_points", "inserted_points", "payload_sha256"}
    assert response.json()["inserted_points"] == 1
    assert not (legacy / "metadata.sqlite3").exists()
    with connect_operational(database) as db:
        assert db.execute("SELECT COUNT(*) FROM metric_versions").fetchone() == (1,)


def test_madrid_route_converts_utc_instant_across_dst_and_groups_local_day(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HEALTH_TIMEZONE", "Europe/Madrid")
    module, _, database = build_pointer_app(monkeypatch, tmp_path)
    module.store._clock = lambda: datetime(2026, 3, 29, 1, 30, tzinfo=UTC)

    converted = live_ingestion._row_local_timestamp("2026-03-29T01:30:00Z", module.store._timezone)
    response = TestClient(module.app).post(
        "/v1/ingest",
        content=payload(metric("step_count", "count", {"qty": 1, "date": "2026-03-29T01:30:00Z"})),
        headers={"Authorization": f"Bearer {TOKEN}", **SOURCE},
    )

    assert converted.isoformat() == "2026-03-29T03:30:00+02:00"
    assert response.status_code == 200
    with connect_operational(database) as db:
        assert db.execute("SELECT local_date FROM metric_versions").fetchone() == ("2026-03-29",)


@pytest.mark.parametrize("row_date", ("2026-03-29T03:30:00", "not-a-timestamp"))
def test_live_ingestion_rejects_naive_and_invalid_timestamps(tmp_path: Path, row_date: str):
    runtime, _ = create_runtime(tmp_path)

    with pytest.raises(LiveIngestError) as error:
        runtime.ingest(payload(metric("step_count", "count", {"qty": 1, "date": row_date})), SOURCE)

    assert error.value.status_code == 422


def test_unverified_candidate_is_rejected_before_store_startup(monkeypatch, tmp_path: Path):
    with pytest.raises(RuntimeError, match="state"):
        build_pointer_app(monkeypatch, tmp_path, state="building")


def test_declared_and_actual_body_limits_stop_streaming(monkeypatch, tmp_path: Path):
    module, _, database = build_pointer_app(monkeypatch, tmp_path)
    module.MAX_BODY = 5
    authorization = (b"authorization", f"Bearer {TOKEN}".encode())
    calls = 0

    async def forbidden_receive():
        raise AssertionError("declared oversized body was consumed")

    declared = Request(
        {"type": "http", "method": "POST", "path": "/v1/ingest", "headers": [authorization, (b"content-length", b"6")]},
        forbidden_receive,
    )
    with pytest.raises(module.HTTPException) as declared_error:
        anyio.run(module.ingest, declared)
    assert declared_error.value.status_code == 413

    messages = iter(
        (
            {"type": "http.request", "body": b"123", "more_body": True},
            {"type": "http.request", "body": b"456", "more_body": True},
            {"type": "http.request", "body": b"private", "more_body": False},
        )
    )

    async def receive():
        nonlocal calls
        calls += 1
        return next(messages)

    actual = Request(
        {"type": "http", "method": "POST", "path": "/v1/ingest", "headers": [authorization]},
        receive,
    )
    with pytest.raises(module.HTTPException) as actual_error:
        anyio.run(module.ingest, actual)
    assert actual_error.value.status_code == 413
    assert calls == 2
    with connect_operational(database) as db:
        assert db.execute("SELECT COUNT(*) FROM import_receipts").fetchone() == (0,)
