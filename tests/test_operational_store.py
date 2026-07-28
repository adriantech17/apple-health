import gzip
import hashlib
import logging
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.operational_store import OperationalStore, ReceiptError, StoreError, VersionCandidate
from src.storage_schema import (
    OperationalWriterLock,
    connect_operational,
    create_operational_database,
)


USER_ID = "primary-user"
NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


def create_store(tmp_path: Path, *, fail_at: str | None = None) -> tuple[OperationalStore, Path]:
    root = tmp_path / "candidate"
    root.mkdir(mode=0o700)
    database = create_operational_database(root, user_id=USER_ID)

    def fault(point: str) -> None:
        if point == fail_at:
            raise RuntimeError("synthetic fault")

    return OperationalStore(database, user_id=USER_ID, fault=fault), database


def record(store: OperationalStore, body: bytes, receipt_id: str, **overrides: object):
    arguments = {
        "kind": "live",
        "parser_version": "1",
        "contract_version": "1",
        "source_metadata": {"automation": "synthetic"},
        "result": "accepted",
        "received_at": NOW,
        "contract_valid": True,
    }
    arguments.update(overrides)
    return store.record_receipt(body, receipt_id=receipt_id, **arguments)


def counts(database: Path) -> tuple[int, int, int, int]:
    with connect_operational(database) as db:
        return tuple(
            db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("imports", "import_receipts", "artifacts", "receipt_artifacts")
        )


def candidate(
    value: str | None,
    token: str,
    *,
    completeness: str = "complete",
    validation_status: str = "valid",
) -> VersionCandidate:
    return VersionCandidate(
        metric="step_count",
        local_date="2026-07-27",
        version_kind="absence" if value is None else "value",
        source_unit=None if value is None else "count",
        canonical_unit=None if value is None else "count",
        canonical_value=value,
        details_json=None if value is None else "{}",
        context_fingerprint=hashlib.sha256(token.encode()).hexdigest(),
        completeness=completeness,
        validation_status=validation_status,
    )


def current(database: Path) -> tuple[str, str | None, str, int] | None:
    with connect_operational(database) as db:
        return db.execute(
            """SELECT v.version_kind, v.canonical_value, v.completeness,
                      COALESCE(v.live_authority_sequence, v.batch_authority_sequence)
               FROM metric_current AS c
               JOIN metric_versions AS v ON v.version_id=c.version_id"""
        ).fetchone()


def test_owner_hash_import_is_reused_while_receipts_remain_distinct(tmp_path: Path):
    store, database = create_store(tmp_path)
    body = b'{"synthetic":1}'

    first = record(store, body, "receipt-1")
    second = record(store, body, "receipt-2")

    assert first.import_id == second.import_id
    assert first.duplicate_import is False
    assert second.duplicate_import is True
    assert counts(database) == (1, 2, 1, 2)
    artifact = next((database.parent / "raw-v2" / "sha256").glob("*/*.json.gz"))
    assert gzip.decompress(artifact.read_bytes()) == body
    assert stat.S_IMODE(artifact.stat().st_mode) == 0o600


def test_rejected_raw_retention_depends_on_validated_contract(tmp_path: Path):
    store, database = create_store(tmp_path)

    malformed = record(
        store,
        b"not-json",
        "receipt-malformed",
        result="rejected",
        contract_valid=False,
        errors=(ReceiptError("invalid_json"),),
    )
    all_invalid = record(
        store,
        b'{"synthetic":"all-invalid"}',
        "receipt-all-invalid",
        result="rejected",
        contract_valid=True,
        errors=(ReceiptError("invalid_unit", "step_count", "2026-07-28"),),
    )

    assert malformed.artifact_retained is False
    assert all_invalid.artifact_retained is True
    assert counts(database) == (2, 2, 1, 1)
    with connect_operational(database) as db:
        assert db.execute(
            "SELECT code, metric, local_date FROM receipt_errors ORDER BY receipt_id"
        ).fetchall() == [
            ("invalid_unit", "step_count", "2026-07-28"),
            ("invalid_json", None, None),
        ]


@pytest.mark.parametrize(
    "fault_point,published",
    [
        ("after_stage_write", False),
        ("after_stage_sync", False),
        ("after_rename", True),
        ("after_parent_sync", True),
        ("before_sqlite_commit", True),
    ],
)
def test_artifact_faults_never_publish_sqlite_state_and_orphans_are_quarantined(
    tmp_path: Path, fault_point: str, published: bool
):
    store, database = create_store(tmp_path, fail_at=fault_point)

    with pytest.raises(RuntimeError, match="synthetic fault"):
        record(store, b'{"synthetic":2}', "receipt-fault")

    assert counts(database) == (0, 0, 0, 0)
    assert store.quarantine_orphans() == (1 if published else 0)
    assert not list((database.parent / "raw-v2").glob("**/*.staging"))


@pytest.mark.parametrize("operation,published", [("open", False), ("rename", False), ("fsync", True)])
def test_publication_oserror_is_private_and_preserves_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str, published: bool
):
    store, database = create_store(tmp_path)
    body = b'{"synthetic":"private-publication-error"}'
    digest = hashlib.sha256(body).hexdigest()
    parent = database.parent
    for part in ("raw-v2", "sha256", digest[:2]):
        parent /= part
        parent.mkdir(mode=0o700)
    original = getattr(os, operation)
    calls = 0

    def fail_publication(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        should_fail = operation == "rename" or (
            operation == "open" and str(args[0]).endswith(".staging")
        ) or (operation == "fsync" and calls == 2)
        if should_fail:
            raise OSError(f"{parent}/.{digest}.private-value")
        return original(*args, **kwargs)

    monkeypatch.setattr(os, operation, fail_publication)
    with pytest.raises(StoreError, match="^Artifact publication failed$"):
        record(store, body, "receipt-publication-error")

    assert counts(database) == (0, 0, 0, 0)
    assert not list(parent.glob("*.staging"))
    assert store.quarantine_orphans() == (1 if published else 0)


def test_existing_artifact_is_reused_only_after_private_content_verification(tmp_path: Path):
    store, database = create_store(tmp_path)
    body = b'{"synthetic":3}'
    record(store, body, "receipt-1")
    artifact = next((database.parent / "raw-v2" / "sha256").glob("*/*.json.gz"))
    artifact.write_bytes(gzip.compress(b"different", mtime=0))

    with pytest.raises(StoreError, match="Stored artifact verification failed") as error:
        record(store, body, "receipt-2")

    assert counts(database) == (1, 1, 1, 1)
    assert str(artifact) not in str(error.value)
    assert store.quarantine_orphans() == 0


def test_diagnostics_are_sanitized_and_full_durability_is_preserved(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
):
    store, database = create_store(tmp_path)
    private_value = "private-synthetic-value"
    caplog.set_level(logging.DEBUG)

    with pytest.raises(ValueError, match="Invalid receipt error") as error:
        record(
            store,
            private_value.encode(),
            "receipt-private",
            result="rejected",
            contract_valid=False,
            errors=(ReceiptError(private_value),),
        )

    assert private_value not in str(error.value)
    assert private_value not in caplog.text
    with connect_operational(database) as db:
        assert db.execute("PRAGMA synchronous").fetchone() == (2,)


def test_context_retry_is_idempotent_but_completeness_change_gets_authority(tmp_path: Path):
    store, database = create_store(tmp_path)
    body = b'{"synthetic":"versions"}'

    first = record(
        store,
        body,
        "receipt-1",
        versions=(candidate("10", "partial", completeness="partial"),),
    )
    duplicate = record(
        store,
        body,
        "receipt-2",
        versions=(candidate("10", "partial", completeness="partial"),),
    )
    corrected = record(
        store,
        body,
        "receipt-3",
        versions=(candidate("10", "complete"),),
    )

    assert (first.inserted_versions, first.authority_sequence) == (1, 1)
    assert (duplicate.inserted_versions, duplicate.authority_sequence) == (0, None)
    assert (corrected.inserted_versions, corrected.authority_sequence) == (1, 2)
    assert current(database) == ("value", "10", "complete", 2)
    with connect_operational(database) as db:
        assert db.execute("SELECT next_authority_sequence FROM users").fetchone() == (3,)
        assert db.execute("SELECT COUNT(*) FROM metric_versions").fetchone() == (2,)


def test_replay_does_not_suppress_later_live_authority(tmp_path: Path):
    store, database = create_store(tmp_path)
    body = b'{"synthetic":"replay-first"}'

    replay = record(
        store,
        body,
        "receipt-replay",
        kind="replay",
        versions=(candidate("10", "shared", validation_status="replay"),),
    )
    live = record(store, body, "receipt-live", versions=(candidate("10", "shared"),))

    assert (replay.inserted_versions, replay.authority_sequence) == (1, None)
    assert (live.inserted_versions, live.authority_sequence) == (1, 1)
    assert current(database) == ("value", "10", "complete", 1)


def test_complete_current_never_regresses_and_later_complete_correction_wins(tmp_path: Path):
    store, database = create_store(tmp_path)

    for ordinal, item in enumerate(
        (
            candidate("10", "partial-1", completeness="partial"),
            candidate("20", "complete-2"),
            candidate("30", "unknown-3", completeness="unknown"),
            candidate("40", "complete-4"),
        ),
        start=1,
    ):
        record(
            store,
            f'{{"receipt":{ordinal}}}'.encode(),
            f"receipt-{ordinal}",
            versions=(item,),
        )
        if ordinal == 3:
            assert current(database) == ("value", "20", "complete", 2)

    assert current(database) == ("value", "40", "complete", 4)


def test_replay_and_unresolved_conflicts_never_advance_current(tmp_path: Path):
    store, database = create_store(tmp_path)
    replay = record(
        store,
        b'{"synthetic":"replay"}',
        "receipt-replay",
        kind="replay",
        versions=(candidate("90", "replay", validation_status="replay"),),
    )
    conflict = record(
        store,
        b'{"synthetic":"conflict"}',
        "receipt-conflict",
        versions=(candidate("10", "left"), candidate("11", "right")),
    )

    assert (replay.inserted_versions, replay.authority_sequence) == (1, None)
    assert (conflict.inserted_versions, conflict.authority_sequence) == (0, None)
    assert current(database) is None
    with connect_operational(database) as db:
        assert db.execute("SELECT code FROM receipt_errors").fetchall() == [
            ("unresolved_conflict",)
        ]
        assert db.execute("SELECT next_authority_sequence FROM users").fetchone() == (1,)


def test_live_receipts_cannot_assert_authoritative_absence(tmp_path: Path):
    store, database = create_store(tmp_path)

    with pytest.raises(ValueError, match="Invalid metric version"):
        record(
            store,
            b'{"synthetic":"live-tombstone"}',
            "receipt-live-tombstone",
            versions=(candidate(None, "live-tombstone"),),
        )

    assert counts(database) == (0, 0, 0, 0)


def test_rejected_receipts_cannot_persist_metric_versions(tmp_path: Path):
    store, database = create_store(tmp_path)

    with pytest.raises(ValueError, match="Invalid receipt context"):
        record(
            store,
            b'{"synthetic":"rejected-version"}',
            "receipt-rejected-version",
            result="rejected",
            versions=(candidate("10", "rejected-version"),),
        )

    assert counts(database) == (0, 0, 0, 0)


@pytest.mark.parametrize("fault_point", ["after_authority", "after_versions", "after_projection"])
def test_every_projection_fault_rolls_back_receipt_versions_authority_and_current(
    tmp_path: Path, fault_point: str
):
    store, database = create_store(tmp_path, fail_at=fault_point)

    with pytest.raises(RuntimeError, match="synthetic fault"):
        record(
            store,
            b'{"synthetic":"rollback"}',
            "receipt-fault",
            versions=(candidate("10", fault_point),),
        )

    with connect_operational(database) as db:
        assert tuple(
            db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("imports", "import_receipts", "authority_events", "metric_versions", "metric_current")
        ) == (0, 0, 0, 0, 0)
        assert db.execute("SELECT next_authority_sequence FROM users").fetchone() == (1,)


def test_shared_projection_uses_one_promoted_batch_tombstone_and_ignores_pending(
    tmp_path: Path,
):
    store, database = create_store(tmp_path)
    record(
        store,
        b'{"synthetic":"live"}',
        "receipt-live",
        versions=(candidate("10", "live"),),
    )
    digest = "b" * 64
    with OperationalWriterLock(database.parent) as writer:
        with connect_operational(database, read_only=False, writer=writer) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO imports VALUES ('batch-import', ?, ?, 1, '2026-07-28T12:01:00Z')",
                (USER_ID, digest),
            )
            db.execute(
                "INSERT INTO reconciliation_batches VALUES ('batch-1',?,'reconciliation',?,'{}','pending',NULL,NULL,NULL)",
                (USER_ID, "c" * 64),
            )
            for receipt_id in ("batch-selected", "batch-unselected"):
                db.execute(
                    """INSERT INTO import_receipts
                       (receipt_id,user_id,import_id,batch_id,kind,parser_version,contract_version,
                        source_metadata_json,result,received_at,committed_at)
                       VALUES (? ,?,'batch-import','batch-1','reconciliation','1','1','{}','accepted',
                               '2026-07-28T12:01:00Z','2026-07-28T12:01:00Z')""",
                    (receipt_id, USER_ID),
                )
            db.execute(
                "UPDATE reconciliation_batches SET status='sealed',approval_sha256=?,authority_sequence=2,sealed_at='2026-07-28T12:02:00Z'",
                ("d" * 64,),
            )
            db.execute(
                "INSERT INTO authority_events (user_id,authority_sequence,batch_id,batch_kind,created_at) VALUES (?,2,'batch-1','reconciliation','2026-07-28T12:02:00Z')",
                (USER_ID,),
            )
            db.execute("UPDATE users SET next_authority_sequence=3 WHERE user_id=?", (USER_ID,))
            db.execute(
                """INSERT INTO metric_versions
                   (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,
                    context_fingerprint,completeness,validation_status,batch_authority_sequence)
                   VALUES ('batch-tombstone',?,'batch-selected','batch-1','step_count','2026-07-27',
                           'absence',?,'complete','valid',2)""",
                (USER_ID, hashlib.sha256(b"tombstone").hexdigest()),
            )
            other = candidate("99", "unselected")
            db.execute(
                """INSERT INTO metric_versions
                   (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,source_unit,
                    canonical_unit,canonical_value,details_json,context_fingerprint,completeness,
                    validation_status,batch_authority_sequence)
                   VALUES ('batch-other',?,'batch-unselected','batch-1','step_count','2026-07-27',
                           'value','count','count','99','{}',?,'complete','valid',2)""",
                (USER_ID, other.context_fingerprint),
            )
            db.execute(
                "INSERT INTO batch_promotions (user_id,batch_id,metric,local_date,version_id) VALUES (?,'batch-1','step_count','2026-07-27','batch-tombstone')",
                (USER_ID,),
            )
            db.execute(
                """INSERT INTO metric_versions
                   (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,
                    context_fingerprint,completeness,validation_status)
                   VALUES ('pending',?,'batch-selected','batch-1','heart_rate','2026-07-27',
                           'absence',?,'complete','pending')""",
                (USER_ID, hashlib.sha256(b"pending").hexdigest()),
            )
            db.commit()

    store.rebuild_current()

    assert current(database) == ("absence", None, "complete", 2)
    with connect_operational(database) as db:
        assert db.execute("SELECT version_id FROM metric_current").fetchall() == [
            ("batch-tombstone",)
        ]
