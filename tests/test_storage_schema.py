import os
import sqlite3
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.storage_schema import (
    OperationalWriterLock,
    connect_operational,
    create_operational_database,
    validate_operational_database,
)


USER_ID = "primary-user"
HASH_A = "a" * 64
HASH_B = "b" * 64

@contextmanager
def writable(path: Path):
    with OperationalWriterLock(path.parent) as writer:
        with connect_operational(path, read_only=False, writer=writer) as db:
            yield db

def create_database(tmp_path: Path) -> Path:
    root = tmp_path / "candidate"
    root.mkdir(mode=0o700)
    path = create_operational_database(root, user_id=USER_ID)
    return path

def insert_import(db: sqlite3.Connection, import_id: str = "import-1") -> None:
    db.execute(
        "INSERT INTO imports VALUES (?, ?, ?, ?, ?)",
        (import_id, USER_ID, HASH_A, 100, "2026-07-21T12:00:00Z"),
    )

def insert_receipt(db: sqlite3.Connection, receipt_id: str, *, kind: str = "live", import_id: str = "import-1") -> None:
    db.execute(
        """INSERT INTO import_receipts (
               receipt_id, user_id, import_id, kind, parser_version,
               contract_version, source_metadata_json, result, received_at
           ) VALUES (?, ?, ?, ?, '1', '1', '{}', 'accepted', ?)""",
        (receipt_id, USER_ID, import_id, kind, "2026-07-21T12:01:00Z"),
    )

def insert_live_authority(db: sqlite3.Connection, receipt_id: str, sequence: int = 1) -> None:
    db.execute(
        """INSERT INTO authority_events (
               user_id, authority_sequence, live_receipt_id,
               live_receipt_kind, created_at
           ) VALUES (?, ?, ?, 'live', ?)""",
        (USER_ID, sequence, receipt_id, "2026-07-21T12:02:00Z"),
    )

def insert_value_version(db: sqlite3.Connection, version_id: str, receipt_id: str, *, metric: str = "step_count", local_date: str = "2026-07-20", sequence: int = 1) -> None:
    db.execute(
        """INSERT INTO metric_versions (
               version_id, user_id, receipt_id, metric, local_date, version_kind,
               source_unit, canonical_unit, canonical_value, details_json,
               context_fingerprint, completeness, validation_status,
               live_authority_sequence
           ) VALUES (?, ?, ?, ?, ?, 'value', 'count', 'count', '123', '{}',
                     ?, 'complete', 'valid', ?)""",
        (version_id, USER_ID, receipt_id, metric, local_date, HASH_B, sequence),
    )

def test_explicit_creation_is_idempotent_and_does_not_touch_legacy(tmp_path: Path):
    legacy = tmp_path / "legacy"
    legacy.mkdir(mode=0o700)
    legacy_db = legacy / "metadata.sqlite3"
    with sqlite3.connect(legacy_db) as db:
        db.execute("CREATE TABLE evidence (value TEXT NOT NULL)")
        db.execute("INSERT INTO evidence VALUES ('synthetic')")
    legacy_before = legacy_db.read_bytes()

    path = create_database(tmp_path)
    first_schema = path.read_bytes()
    second_path = create_operational_database(path.parent, user_id=USER_ID)

    assert second_path == path
    assert path.name == "operational.sqlite3"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert legacy_db.read_bytes() == legacy_before
    with sqlite3.connect(f"file:{legacy_db}?mode=ro", uri=True) as db:
        assert db.execute("SELECT value FROM evidence").fetchone() == ("synthetic",)
    assert path.read_bytes() == first_schema
    linked_root = tmp_path / "linked"
    linked_root.mkdir(mode=0o700)
    os.link(path, linked_root / "operational.sqlite3")
    with pytest.raises(RuntimeError, match="private regular file"):
        validate_operational_database(linked_root / "operational.sqlite3", user_id=USER_ID)
    (linked_root / "operational.sqlite3").unlink()

    with connect_operational(path, read_only=True) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        assert set("""schema_migrations users dataset_state imports artifacts receipt_artifacts
import_receipts receipt_errors authority_events metric_versions metric_current reconciliation_batches
batch_sources batch_promotions semantic_evidence replay_operations live_freshness""".split()) <= tables
        assert db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone() == (1,)
        assert db.execute("SELECT user_id, timezone FROM users").fetchone() == (USER_ID, "Europe/Madrid")
        assert db.execute("SELECT state FROM dataset_state").fetchone() == ("building",)

def test_connection_policy_and_required_indexes(tmp_path: Path):
    path = create_database(tmp_path)
    with writable(path) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert db.execute("PRAGMA synchronous").fetchone() == (2,)
        assert 0 < db.execute("PRAGMA busy_timeout").fetchone()[0] <= 30_000

        indexes = {row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='index'")}
        assert {"idx_receipts_import", "idx_receipts_status_time", "idx_versions_identity", "idx_batches_status"} <= indexes
        db.execute("INSERT INTO imports VALUES ('fractional', ?, ?, 1, '2026-07-21T12:00:00.123456+00:00')", (USER_ID, HASH_A))
        assert all(stat.S_IMODE(Path(f"{path}{suffix}").stat().st_mode) == 0o600 and Path(f"{path}{suffix}").stat().st_nlink == 1 for suffix in ("-wal", "-shm"))
        for import_id, timestamp in (("invalid-date", "2026-02-30T12:00:00Z"), ("invalid-hour", "2026-07-21T24:00:00Z")):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute("INSERT INTO imports VALUES (?, ?, ?, 1, ?)", (import_id, USER_ID, HASH_B, timestamp))

def test_startup_validation_is_read_only_and_rejects_identity_mismatch(tmp_path: Path):
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(RuntimeError, match="unavailable"):
        validate_operational_database(missing, user_id=USER_ID)
    assert not missing.exists()

    path = create_database(tmp_path)
    target = tmp_path / "sidecar"
    target.write_bytes(b"synthetic")
    target.chmod(0o644)
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{path}{suffix}")
        sidecar.unlink(missing_ok=True)
        os.link(target, sidecar)
        with pytest.raises(RuntimeError, match="private regular file"):
            validate_operational_database(path, user_id=USER_ID)
        assert stat.S_IMODE(target.stat().st_mode) == 0o644
        sidecar.unlink()
    before = (path.stat().st_mtime_ns, path.read_bytes())
    validate_operational_database(path, user_id=USER_ID)
    assert (path.stat().st_mtime_ns, path.read_bytes()) == before

    with pytest.raises(RuntimeError, match="identity"):
        validate_operational_database(path, user_id="another-user")
    with pytest.raises(RuntimeError, match="timezone"):
        validate_operational_database(path, user_id=USER_ID, timezone="UTC")

def test_owner_and_current_identity_are_enforced_by_composite_foreign_keys(
    tmp_path: Path,
):
    path = create_database(tmp_path)
    with writable(path) as db:
        insert_import(db)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """INSERT INTO import_receipts (
                       receipt_id, user_id, import_id, kind, parser_version,
                       contract_version, source_metadata_json, result, received_at
                   ) VALUES ('receipt-wrong', 'another-user', 'import-1', 'live',
                             '1', '1', '{}', 'accepted', '2026-07-21T12:01:00Z')"""
            )

        insert_receipt(db, "receipt-1")
        insert_live_authority(db, "receipt-1")
        insert_value_version(db, "version-1", "receipt-1")

        db.execute(
            "INSERT INTO metric_current VALUES (?, ?, ?, ?)",
            (USER_ID, "step_count", "2026-07-20", "version-1"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO metric_current VALUES (?, ?, ?, ?)",
                (USER_ID, "heart_rate", "2026-07-20", "version-1"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO metric_current VALUES (?, ?, ?, ?)",
                (USER_ID, "step_count", "2026-07-19", "version-1"),
            )

def test_authority_source_and_version_lineage_are_relationally_enforced(
    tmp_path: Path,
):
    path = create_database(tmp_path)
    with writable(path) as db:
        insert_import(db)
        insert_receipt(db, "receipt-1")
        insert_receipt(db, "receipt-2")

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO authority_events (user_id, authority_sequence, created_at) VALUES (?, 1, ?)",
                (USER_ID, "2026-07-21T12:02:00Z"),
            )
        insert_live_authority(db, "receipt-1")
        with pytest.raises(sqlite3.IntegrityError):
            insert_value_version(db, "wrong-authority", "receipt-2")
        db.execute("UPDATE import_receipts SET result='rejected' WHERE receipt_id='receipt-2'")
        with pytest.raises(sqlite3.IntegrityError):
            insert_live_authority(db, "receipt-2", 2)

def test_pending_versions_and_unsealed_batches_cannot_become_current(tmp_path: Path):
    path = create_database(tmp_path)
    with writable(path) as db:
        insert_import(db)
        insert_receipt(db, "receipt-1")
        db.execute(
            """INSERT INTO metric_versions (
                   version_id, user_id, receipt_id, metric, local_date,
                   version_kind, context_fingerprint, completeness,
                   validation_status
               ) VALUES ('pending', ?, 'receipt-1', 'step_count', '2026-07-20',
                         'absence', ?, 'complete', 'pending')""",
            (USER_ID, HASH_B),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO metric_current VALUES (?, 'step_count', '2026-07-20', 'pending')",
                (USER_ID,),
            )

        db.execute(
            """INSERT INTO reconciliation_batches (
                   batch_id, user_id, kind, manifest_sha256, scope_json, status
               ) VALUES ('batch-1', ?, 'reconciliation', ?, '{}', 'pending')""",
            (USER_ID, HASH_B),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO semantic_evidence VALUES ('evidence', ?, 'batch-1', ?, ?, ?, '1', 'passed', '{}', '2026-07-21T12:03:00Z')", (USER_ID, HASH_A, HASH_A, HASH_A))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """INSERT INTO authority_events (
                       user_id, authority_sequence, batch_id, batch_kind, created_at
                   ) VALUES (?, 2, 'batch-1', 'reconciliation', '2026-07-21T12:02:00Z')""",
                (USER_ID,),
            )

def test_context_fingerprint_is_unique_per_logical_import_identity(tmp_path: Path):
    path = create_database(tmp_path)
    with writable(path) as db:
        insert_import(db)
        insert_receipt(db, "receipt-1")
        insert_receipt(db, "receipt-2")
        insert_live_authority(db, "receipt-1", 1)
        insert_live_authority(db, "receipt-2", 2)
        insert_value_version(db, "version-1", "receipt-1", sequence=1)
        with pytest.raises(sqlite3.IntegrityError):
            insert_value_version(db, "version-2", "receipt-2", sequence=2)

def test_sealed_batch_authority_cycle_can_commit_atomically(tmp_path: Path):
    path = create_database(tmp_path)
    with writable(path) as db:
        insert_import(db)
        db.execute("INSERT INTO reconciliation_batches (batch_id,user_id,kind,manifest_sha256,scope_json,status) VALUES ('batch-1',?,'reconciliation',?,'{}','pending')", (USER_ID, HASH_B))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO import_receipts (receipt_id,user_id,import_id,batch_id,kind,parser_version,contract_version,source_metadata_json,result,received_at) VALUES ('wrong-kind',?,'import-1','batch-1','backfill','1','1','{}','accepted','2026-07-21T12:01:00Z')", (USER_ID,))
        db.execute("INSERT INTO import_receipts (receipt_id,user_id,import_id,batch_id,kind,parser_version,contract_version,source_metadata_json,result,received_at) VALUES ('receipt-1',?,'import-1','batch-1','reconciliation','1','1','{}','accepted','2026-07-21T12:01:00Z')", (USER_ID,))
        db.execute("INSERT INTO import_receipts (receipt_id,user_id,import_id,batch_id,kind,parser_version,contract_version,source_metadata_json,result,received_at) VALUES ('pending',?,'import-1','batch-1','reconciliation','1','1','{}','pending','2026-07-21T12:01:00Z')", (USER_ID,))
        db.execute("UPDATE reconciliation_batches SET status='sealed',approval_sha256=?,authority_sequence=1,sealed_at='2026-07-21T12:02:00Z' WHERE batch_id='batch-1'", (HASH_A,))
        db.execute("INSERT INTO authority_events (user_id,authority_sequence,batch_id,batch_kind,created_at) VALUES (?,1,'batch-1','reconciliation','2026-07-21T12:02:00Z')", (USER_ID,))
        db.execute("INSERT INTO metric_versions (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,source_unit,canonical_unit,canonical_value,details_json,context_fingerprint,completeness,validation_status,batch_authority_sequence) VALUES ('version-1',?,'receipt-1','batch-1','step_count','2026-07-20','value','count','count','123','{}',?,'complete','valid',1)", (USER_ID, HASH_B))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO metric_versions (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,source_unit,canonical_unit,canonical_value,details_json,context_fingerprint,completeness,validation_status,batch_authority_sequence) VALUES ('pending-version',?,'pending','batch-1','heart_rate','2026-07-20','value','bpm','bpm','60','{}',?,'complete','valid',1)", (USER_ID, HASH_A))
        db.execute("INSERT INTO batch_promotions (user_id,batch_id,metric,local_date,version_id) VALUES (?,'batch-1','step_count','2026-07-20','version-1')", (USER_ID,))
        db.execute("INSERT INTO metric_current (user_id,metric,local_date,version_id) VALUES (?,'step_count','2026-07-20','version-1')", (USER_ID,))
    with connect_operational(path) as db:
        assert db.execute("SELECT version_id FROM metric_current").fetchone() == ("version-1",)

@pytest.mark.parametrize("columns, values", [
    ("version_kind, source_unit, canonical_unit, canonical_value", ("absence", "count", None, None)),
    ("version_kind, source_unit, canonical_unit, canonical_value", ("value", None, "count", "1")),
    ("version_kind, completeness", ("absence", "future")),
])
def test_version_shape_checks_reject_invalid_rows(tmp_path: Path, columns: str, values: tuple[object, ...]):
    path = create_database(tmp_path)
    with writable(path) as db:
        insert_import(db)
        insert_receipt(db, "receipt-1")
        placeholders = ", ".join("?" for _ in values)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                f"""INSERT INTO metric_versions (
                        version_id, user_id, receipt_id, metric, local_date,
                        context_fingerprint, validation_status, {columns}
                    ) VALUES ('invalid', ?, 'receipt-1', 'step_count',
                              '2026-07-20', ?, 'pending', {placeholders})""",
                (USER_ID, HASH_B, *values),
            )

def test_query_plans_use_identity_join_and_status_indexes(tmp_path: Path):
    path = create_database(tmp_path)
    with connect_operational(path) as db:
        queries = (
            (
                "SELECT version_id FROM metric_current WHERE user_id=? AND metric=? AND local_date BETWEEN ? AND ?",
                (USER_ID, "step_count", "2026-01-01", "2026-12-31"),
            ),
            (
                "SELECT receipt_id FROM import_receipts WHERE user_id=? AND result=? ORDER BY received_at",
                (USER_ID, "accepted"),
            ),
            (
                "SELECT batch_id FROM reconciliation_batches WHERE user_id=? AND status=?",
                (USER_ID, "pending"),
            ),
        )
        for query, parameters in queries:
            plan = " ".join(
                row[3]
                for row in db.execute(f"EXPLAIN QUERY PLAN {query}", parameters)
            )
            assert "USING" in plan and "SCAN" not in plan

        join_plan = " ".join(
            row[3]
            for row in db.execute(
                """EXPLAIN QUERY PLAN
                   SELECT v.canonical_value
                   FROM metric_current AS c
                   JOIN metric_versions AS v ON v.version_id = c.version_id
                   WHERE c.user_id=? AND c.metric=?
                     AND c.local_date BETWEEN ? AND ?""",
                (USER_ID, "step_count", "2026-01-01", "2026-12-31"),
            )
        )
        assert "SEARCH c" in join_plan and "SEARCH v" in join_plan

def test_startup_rejects_missing_indexes_and_foreign_key_corruption(tmp_path: Path):
    path = create_database(tmp_path)
    with writable(path) as db:
        db.execute("DROP INDEX idx_batch_sources")
    with pytest.raises(RuntimeError, match="incomplete"):
        validate_operational_database(path, user_id=USER_ID)

    path = tmp_path / "candidate" / "operational.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE INDEX idx_batch_sources ON batch_sources(user_id, batch_id)")
        db.execute("INSERT INTO live_freshness (user_id) VALUES ('missing-owner')")
    with pytest.raises(RuntimeError, match="foreign keys"):
        validate_operational_database(path, user_id=USER_ID)

    other = tmp_path / "other"
    other.mkdir(mode=0o700)
    other_path = create_operational_database(other, user_id=USER_ID)
    with writable(other_path) as db:
        db.execute("DROP TRIGGER metric_versions_context_unique")
    with pytest.raises(RuntimeError, match="incomplete"):
        validate_operational_database(other_path, user_id=USER_ID)

def test_writer_lock_is_exclusive_and_rejects_symlink(tmp_path: Path):
    root = tmp_path / "candidate"
    root.mkdir(mode=0o700)
    path = create_operational_database(root, user_id=USER_ID)
    first = OperationalWriterLock(root)
    second = OperationalWriterLock(root)

    with first:
        with pytest.raises(RuntimeError, match="already active"):
            second.acquire()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(RuntimeError, match="another thread"):
                executor.submit(first.release).result()
        result = subprocess.run(
            [sys.executable, "-c", "from pathlib import Path; from src.storage_schema import OperationalWriterLock; OperationalWriterLock(Path(__import__('sys').argv[1])).acquire()", str(root)],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(connect_operational, path, read_only=False, writer=first)
            with pytest.raises(RuntimeError, match="lock is required"):
                future.result()
        connection = connect_operational(path, read_only=False, writer=first)
        with pytest.raises(RuntimeError, match="still active"):
            first.release()
        connection.close()
        connection = connect_operational(path, read_only=False, writer=first)
        with ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(sqlite3.ProgrammingError):
                executor.submit(connection.close).result()
        with pytest.raises(RuntimeError, match="still active"):
            first.release()
        connection.close()
    with second:
        pass

    lock_path = root / "operational.writer.lock"
    lock_path.unlink()
    target = tmp_path / "target"
    target.write_text("synthetic")
    target.chmod(0o644)
    os.link(target, lock_path)
    with pytest.raises(RuntimeError, match="private regular file"):
        OperationalWriterLock(root).acquire()
    assert stat.S_IMODE(target.stat().st_mode) == 0o644
    lock_path.unlink()
    os.symlink(target, lock_path)
    with pytest.raises(RuntimeError, match="private regular file"):
        OperationalWriterLock(root).acquire()

def test_concurrent_creation_converges_on_one_database(tmp_path: Path):
    root = tmp_path / "candidate"
    root.mkdir(mode=0o700)
    with ThreadPoolExecutor(max_workers=2) as executor:
        paths = list(
            executor.map(
                lambda _: create_operational_database(root, user_id=USER_ID),
                range(2),
            )
        )
    assert paths == [root / "operational.sqlite3"] * 2
