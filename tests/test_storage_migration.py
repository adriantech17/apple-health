from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import scripts.migrate_storage as migration
from src.reconciliation import ReconciliationError, seal_reconciliation
from src.storage_schema import connect_operational


USER_ID = "primary-user"

def test_reference_decimal_preserves_integral_zeroes():
    assert migration._decimal(20) == "20"

def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
def private_file(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    path.chmod(0o600)
    return path

def value_version(metric: str, local_date: str, value: str, token: str) -> dict[str, object]:
    return {
        "canonical_unit": "count",
        "canonical_value": value,
        "completeness": "complete",
        "context_fingerprint": hashlib.sha256(token.encode()).hexdigest(),
        "details": {},
        "local_date": local_date,
        "metric": metric,
        "source_unit": "count",
        "version_kind": "value",
    }

def create_migration_fixture(tmp_path: Path) -> dict[str, Any]:
    installation = tmp_path / "installation"
    datasets = installation / "datasets"
    legacy = datasets / "legacy"
    sources = tmp_path / "baseline-sources"
    installation.mkdir(mode=0o700)
    datasets.mkdir(mode=0o700)
    legacy.mkdir(mode=0o700)
    sources.mkdir(mode=0o700)
    (installation / "current").symlink_to(Path("datasets/legacy"))
    metadata = legacy / "metadata.sqlite3"
    db = sqlite3.connect(metadata)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA wal_autocheckpoint=0")
    db.execute("CREATE TABLE legacy_receipts (receipt_id TEXT PRIMARY KEY)")
    db.execute("INSERT INTO legacy_receipts VALUES ('committed-in-wal')")
    db.commit()
    for sqlite_file in legacy.glob("metadata.sqlite3*"):
        sqlite_file.chmod(0o600)
    raw = legacy / "raw"
    parquet = legacy / "parquet"
    raw.mkdir(mode=0o700)
    parquet.mkdir(mode=0o700)
    private_file(raw / "synthetic.json.gz", b"synthetic-raw-evidence")
    private_file(parquet / "synthetic.parquet", b"synthetic-parquet-evidence")
    source_entries = []
    identities = []
    for ordinal in range(6):
        local_date = f"2025-01-{ordinal + 1:02d}"
        payload = canonical(
            {
                "data": {
                    "metrics": [
                        {
                            "data": [{"date": local_date, "qty": ordinal + 1}],
                            "name": "step_count",
                            "units": "count",
                        }
                    ]
                }
            }
        )
        name = f"synthetic-{ordinal}.json"
        private_file(sources / name, payload)
        source_entries.append({"name": name, "sha256": hashlib.sha256(payload).hexdigest()})
        identities.append({"local_date": local_date, "metric": "step_count", "state": "value"})
    manifest = {
        "batch_id": "synthetic-six-source-baseline",
        "expected_counts": {"identities": 6, "sources": 6},
        "generation_context": {"generator": "synthetic-test"},
        "identities": identities,
        "importer_version": "1",
        "kind": "reconciliation",
        "owner": USER_ID,
        "required_evidence": ["semantic_comparison"],
        "schema_version": 1,
        "scope": {
            "end_date": "2025-12-31",
            "metrics": ["step_count"],
            "start_date": "2025-01-01",
        },
        "sources": source_entries,
        "timezone": "Europe/Madrid",
    }
    manifest_path = private_file(tmp_path / "baseline-manifest.json", canonical(manifest))
    live_body = b'{"synthetic":"live"}'
    backfill_body = b'{"synthetic":"backfill"}'
    reconstruction = {
        "backfill_batches": [
            {
                "authority_sequence": 3,
                "batch_id": "accepted-backfill-1",
                "manifest_sha256": "b" * 64,
                "receipt": {
                    "import_id": "backfill-import-1",
                    "payload_bytes": len(backfill_body),
                    "payload_sha256": hashlib.sha256(backfill_body).hexdigest(),
                    "receipt_id": "backfill-receipt-1",
                    "received_at": "2026-01-03T12:00:00Z",
                },
                "sealed_at": "2026-01-03T12:05:00Z",
                "versions": [
                    value_version("step_count", "2026-01-01", "30", "backfill"),
                    {
                        "canonical_unit": None, "canonical_value": None,
                        "completeness": "complete", "details": None,
                        "context_fingerprint": hashlib.sha256(b"absence").hexdigest(),
                        "local_date": "2026-01-02", "metric": "vo2_max",
                        "source_unit": None, "version_kind": "absence",
                    },
                ],
            }
        ],
        "evidence_gaps": [
            {"code": "pruned_raw", "population": "live"},
            {"code": "collapsed_occurrence", "population": "live"},
        ],
        "expected_legacy_corrections": ["legacy_daily_aggregation"],
        "freshness": {
            "latest_authenticated_receipt_id": "live-receipt-1",
            "latest_clean_receipt_id": "live-receipt-1",
            "latest_committed_receipt_id": "live-receipt-1",
            "latest_complete_local_date": "2026-01-01",
        },
        "live_receipts": [
            {
                "authority_sequence": 2,
                "import_id": "live-import-1",
                "payload_bytes": len(live_body),
                "payload_sha256": hashlib.sha256(live_body).hexdigest(),
                "received_at": "2026-01-02T12:00:00Z",
                "receipt_id": "live-receipt-1",
                "result": "accepted",
                "versions": [value_version("step_count", "2026-01-01", "20", "live")],
            }
        ],
        "owner": USER_ID,
        "schema_version": 1,
        "timezone": "Europe/Madrid",
    }
    reconstruction_path = private_file(
        tmp_path / "reconstruction.json", canonical(reconstruction)
    )
    return {
        "installation": installation,
        "keeper": db,
        "legacy": legacy,
        "manifest": manifest_path,
        "reconstruction": reconstruction_path,
        "sources": sources,
    }

def legacy_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.name.endswith("-shm")
    }

def build(paths: dict[str, Any], **kwargs):
    return migration.build_candidate(
        paths["installation"],
        paths["manifest"],
        paths["sources"],
        paths["reconstruction"],
        user_id=USER_ID,
        **kwargs,
    )

def test_builds_wal_consistent_candidate_and_preserves_reconstruction_populations(
    tmp_path: Path,
):
    paths = create_migration_fixture(tmp_path)
    before = legacy_hashes(paths["legacy"])
    result = build(paths)
    assert result.resumed is False
    assert result.phase == "complete"
    assert result.source_files == len(before)
    assert result.evidence_gaps == 2
    assert len(result.source_watermark) == len(result.candidate_sha256) == 64
    assert legacy_hashes(paths["legacy"]) == before
    assert migration.MaintenanceGate(paths["installation"]).active
    candidate = paths["installation"] / "datasets" / "candidate"
    with sqlite3.connect(candidate / "metadata.sqlite3") as frozen:
        assert frozen.execute("SELECT receipt_id FROM legacy_receipts").fetchall() == [
            ("committed-in-wal",)
        ]
    with connect_operational(candidate / "operational.sqlite3") as db:
        assert db.execute("SELECT state,source_watermark FROM dataset_state").fetchone() == (
            "building",
            result.source_watermark,
        )
        assert db.execute("SELECT COUNT(*) FROM batch_sources").fetchone() == (6,)
        assert db.execute(
            "SELECT receipt_id,kind,received_at FROM import_receipts WHERE kind='live'"
        ).fetchall() == [("live-receipt-1", "live", "2026-01-02T12:00:00Z")]
        assert db.execute(
            "SELECT batch_id,kind,authority_sequence FROM reconciliation_batches ORDER BY batch_id"
        ).fetchall() == [
            ("accepted-backfill-1", "backfill", 3),
            ("synthetic-six-source-baseline", "reconciliation", None),
        ]
        assert db.execute(
            "SELECT authority_sequence FROM authority_events ORDER BY authority_sequence"
        ).fetchall() == [(2,), (3,)]
        assert db.execute(
            "SELECT latest_authenticated_receipt_id,latest_committed_receipt_id,latest_clean_receipt_id,latest_complete_local_date FROM live_freshness"
        ).fetchone() == (
            "live-receipt-1",
            "live-receipt-1",
            "live-receipt-1",
            "2026-01-01",
        )
        assert db.execute("SELECT COUNT(*) FROM replay_operations").fetchone() == (0,)

def test_interrupted_build_resumes_exactly_once_and_refuses_source_drift(tmp_path: Path, monkeypatch):
    paths = create_migration_fixture(tmp_path)
    before = legacy_hashes(paths["legacy"])
    write = migration.os.write
    monkeypatch.setattr(migration.os, "write", lambda descriptor, content: write(descriptor, content[:max(1, len(content) // 2)]))
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        build(
            paths,
            fault=lambda point: (_ for _ in ()).throw(RuntimeError("synthetic interruption"))
            if point == "before_reconstruction_commit"
            else None,
        )
    first = build(paths)
    resumed = build(paths)
    assert first.phase == resumed.phase == "complete"
    assert resumed.resumed is True
    assert resumed.candidate_sha256 == first.candidate_sha256
    assert legacy_hashes(paths["legacy"]) == before
    candidate_db = paths["installation"] / "datasets" / "candidate" / "operational.sqlite3"
    with connect_operational(candidate_db) as db:
        assert db.execute("SELECT COUNT(*) FROM import_receipts WHERE kind='live'").fetchone() == (1,)
        assert db.execute("SELECT COUNT(*) FROM reconciliation_batches WHERE kind='backfill'").fetchone() == (1,)
    private_file(paths["legacy"] / "raw" / "synthetic.json.gz", b"changed-source")
    with pytest.raises(migration.MigrationError, match="^Legacy source changed$"):
        build(paths)

def test_resume_after_reconstruction_commit_is_idempotent(tmp_path: Path):
    paths = create_migration_fixture(tmp_path)
    with pytest.raises(RuntimeError, match="synthetic post-commit interruption"):
        build(
            paths,
            fault=lambda point: (_ for _ in ()).throw(
                RuntimeError("synthetic post-commit interruption")
            )
            if point == "after_reconstruction_commit"
            else None,
        )
    resumed = build(paths)
    assert (resumed.resumed, resumed.phase) == (True, "complete")
    database = paths["installation"] / "datasets" / "candidate" / "operational.sqlite3"
    with connect_operational(database) as db:
        assert db.execute("SELECT COUNT(*) FROM import_receipts WHERE kind='live'").fetchone() == (1,)
        assert db.execute("SELECT COUNT(*) FROM reconciliation_batches WHERE kind='backfill'").fetchone() == (1,)

def test_candidate_builder_requires_adopted_legacy_layout(tmp_path: Path):
    paths = create_migration_fixture(tmp_path)
    current = paths["installation"] / "current"
    current.unlink()
    (paths["installation"] / "datasets" / "candidate").mkdir(mode=0o700)
    current.symlink_to(Path("datasets/candidate"))
    with pytest.raises(migration.MigrationError, match="^Legacy dataset must remain selected$"):
        build(paths)

def test_independent_comparator_persists_manifest_bound_sanitized_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    paths = create_migration_fixture(tmp_path)
    built = build(paths)
    database = paths["installation"] / "datasets" / "candidate" / "operational.sqlite3"
    report = tmp_path / "comparison.json"
    monkeypatch.setattr(migration, "apply_projection", lambda *_: pytest.fail("operational selector used"))
    result = migration.compare_candidate(
        database,
        paths["manifest"],
        paths["sources"],
        paths["reconstruction"],
        report,
        created_at=datetime(2026, 1, 4, tzinfo=UTC),
    )
    assert (result.passed, result.differences, result.expected_legacy_corrections) == (True, 0, 1)
    assert report.stat().st_mode & 0o777 == 0o600
    recorded = json.loads(report.read_bytes())
    assert recorded == {
        "checks": result.checks,
        "differences": [],
        "expected_legacy_corrections": ["legacy_daily_aggregation"],
        "outcome": "passed",
        "schema_version": 1,
    }
    assert "20" not in report.read_text() and "30" not in report.read_text()
    with connect_operational(database) as db:
        evidence = db.execute(
            "SELECT manifest_sha256,candidate_sha256,source_set_sha256,outcome,counts_json FROM semantic_evidence"
        ).fetchone()
        assert evidence[:4] == (
            hashlib.sha256(paths["manifest"].read_bytes()).hexdigest(),
            result.candidate_sha256,
            result.source_set_sha256,
            "passed",
        )
        assert json.loads(evidence[4])["snapshot_sha256"]
        assert db.execute("SELECT source_watermark FROM dataset_state").fetchone() == (
            built.source_watermark,
        )

def test_comparator_detects_context_fingerprint_corruption(tmp_path: Path):
    paths = create_migration_fixture(tmp_path)
    build(paths)
    candidate = paths["installation"] / "datasets" / "candidate"
    database = candidate / "operational.sqlite3"
    with migration.OperationalWriterLock(candidate, blocking=True) as writer:
        with migration.connect_operational(database, read_only=False, writer=writer) as db:
            db.execute(
                "UPDATE metric_versions SET context_fingerprint=? WHERE batch_id=?",
                ("f" * 64, "synthetic-six-source-baseline"),
            )
            db.commit()
    result = migration.compare_candidate(
        database, paths["manifest"], paths["sources"], paths["reconstruction"],
        tmp_path / "context-corruption.json", created_at=datetime(2026, 1, 4, tzinfo=UTC)
    )
    assert result.passed is False
    assert result.checks["versions"] is False

def test_comparator_normalizes_offset_timestamp_to_configured_date(tmp_path: Path):
    paths = create_migration_fixture(tmp_path)
    source = paths["sources"] / "synthetic-5.json"
    payload = json.loads(source.read_bytes())
    payload["data"]["metrics"][0]["data"][0]["date"] = "2025-01-06T23:30:00-05:00"
    source_bytes = canonical(payload)
    private_file(source, source_bytes)
    manifest = json.loads(paths["manifest"].read_bytes())
    manifest["sources"][5]["sha256"] = hashlib.sha256(source_bytes).hexdigest()
    manifest["identities"][5]["local_date"] = "2025-01-07"
    private_file(paths["manifest"], canonical(manifest))
    build(paths)
    database = paths["installation"] / "datasets" / "candidate" / "operational.sqlite3"
    result = migration.compare_candidate(
        database, paths["manifest"], paths["sources"], paths["reconstruction"],
        tmp_path / "offset-date.json", created_at=datetime(2026, 1, 4, tzinfo=UTC)
    )
    assert result.passed is True
    assert result.checks["versions"] is True

def test_failed_recomparison_revokes_prior_pass_for_sealing_without_values(
    tmp_path: Path,
):
    paths = create_migration_fixture(tmp_path)
    build(paths)
    candidate = paths["installation"] / "datasets" / "candidate"
    database = candidate / "operational.sqlite3"
    first = migration.compare_candidate(
        database, paths["manifest"], paths["sources"], paths["reconstruction"],
        tmp_path / "first.json", created_at=datetime(2026, 1, 4, tzinfo=UTC)
    )
    with migration.OperationalWriterLock(candidate, blocking=True) as writer:
        with migration.connect_operational(database, read_only=False, writer=writer) as db:
            db.execute("UPDATE metric_versions SET canonical_value='999999' WHERE receipt_id='live-receipt-1'")
            db.commit()
    second = migration.compare_candidate(
        database, paths["manifest"], paths["sources"], paths["reconstruction"],
        tmp_path / "second.json", created_at=datetime(2026, 1, 5, tzinfo=UTC)
    )
    assert first.passed is True
    assert (second.passed, second.differences) == (False, 1)
    assert second.candidate_sha256 != first.candidate_sha256
    assert "999999" not in (tmp_path / "second.json").read_text()
    with connect_operational(database) as db:
        assert db.execute("SELECT outcome,comparator_version FROM semantic_evidence ORDER BY created_at").fetchall() == [
            ("failed", "reference-1-revoked"), ("failed", "reference-1")
        ]
    approval = hashlib.sha256(paths["manifest"].read_bytes()).hexdigest()
    with pytest.raises(ReconciliationError, match="^Successful semantic evidence is missing$"):
        seal_reconciliation(database, "synthetic-six-source-baseline", approval)
