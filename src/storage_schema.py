from __future__ import annotations

import fcntl
import os
import sqlite3
import stat
import threading
from datetime import UTC, datetime
from pathlib import Path


DATABASE_NAME = "operational.sqlite3"
SCHEMA_VERSION = 1
APPLICATION_ID = 0x41485031
DATASET_TIMEZONE = "Europe/Madrid"
BUSY_TIMEOUT_MS = 5_000

EXPECTED_TABLES = set("""schema_migrations users dataset_state imports artifacts
receipt_artifacts import_receipts receipt_errors authority_events metric_versions
metric_current reconciliation_batches batch_sources batch_promotions semantic_evidence replay_operations live_freshness""".split())
EXPECTED_INDEXES = set("""idx_receipts_import idx_receipts_status_time
idx_versions_identity idx_batches_status idx_versions_receipt idx_batch_sources""".split())
EXPECTED_TRIGGERS = {"metric_versions_context_unique"}

_DDL = (
    """CREATE TABLE schema_migrations (
           version INTEGER PRIMARY KEY CHECK (version > 0),
           applied_at TEXT NOT NULL CHECK (datetime(applied_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', applied_at) = substr(applied_at, 1, 19) AND substr(applied_at, 11, 1) = 'T' AND CAST(substr(applied_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(applied_at, -1) = 'Z' OR substr(applied_at, -6) = '+00:00') AND instr(applied_at, char(0)) = 0)
       )""",
    """CREATE TABLE users (
           user_id TEXT PRIMARY KEY CHECK (length(user_id) BETWEEN 1 AND 128),
           timezone TEXT NOT NULL CHECK (timezone = 'Europe/Madrid'),
           contract_version TEXT NOT NULL CHECK (length(contract_version) > 0),
           next_authority_sequence INTEGER NOT NULL DEFAULT 1
               CHECK (next_authority_sequence >= 1)
       )""",
    """CREATE TABLE imports (
           import_id TEXT PRIMARY KEY,
           user_id TEXT NOT NULL,
           payload_sha256 TEXT NOT NULL
               CHECK (length(CAST(payload_sha256 AS BLOB)) = 64 AND payload_sha256 NOT GLOB '*[^0-9a-f]*'),
           payload_bytes INTEGER NOT NULL CHECK (payload_bytes >= 0),
           first_seen_at TEXT NOT NULL CHECK (datetime(first_seen_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', first_seen_at) = substr(first_seen_at, 1, 19) AND substr(first_seen_at, 11, 1) = 'T' AND CAST(substr(first_seen_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(first_seen_at, -1) = 'Z' OR substr(first_seen_at, -6) = '+00:00') AND instr(first_seen_at, char(0)) = 0),
           UNIQUE (user_id, payload_sha256),
           UNIQUE (user_id, import_id),
           FOREIGN KEY (user_id) REFERENCES users(user_id)
       )""",
    """CREATE TABLE artifacts (
           artifact_sha256 TEXT PRIMARY KEY
               CHECK (length(CAST(artifact_sha256 AS BLOB)) = 64 AND artifact_sha256 NOT GLOB '*[^0-9a-f]*'),
           kind TEXT NOT NULL CHECK (kind IN ('live_raw', 'batch_source')),
           relative_path TEXT NOT NULL UNIQUE
               CHECK (length(relative_path) > 0 AND relative_path NOT LIKE '/%' AND relative_path NOT LIKE '%..%'),
           artifact_bytes INTEGER NOT NULL CHECK (artifact_bytes >= 0)
       )""",
    """CREATE TABLE import_receipts (
           receipt_id TEXT PRIMARY KEY,
           user_id TEXT NOT NULL,
           import_id TEXT NOT NULL,
           batch_id TEXT,
           kind TEXT NOT NULL CHECK (kind IN ('live', 'reconciliation', 'backfill', 'replay')),
           parser_version TEXT NOT NULL CHECK (length(parser_version) > 0),
           contract_version TEXT NOT NULL CHECK (length(contract_version) > 0),
           source_metadata_json TEXT NOT NULL CHECK (json_valid(source_metadata_json)),
           result TEXT NOT NULL CHECK (result IN ('accepted', 'degraded', 'rejected', 'pending')),
           received_at TEXT NOT NULL CHECK (datetime(received_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', received_at) = substr(received_at, 1, 19) AND substr(received_at, 11, 1) = 'T' AND CAST(substr(received_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(received_at, -1) = 'Z' OR substr(received_at, -6) = '+00:00') AND instr(received_at, char(0)) = 0),
           committed_at TEXT CHECK (committed_at IS NULL OR (datetime(committed_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', committed_at) = substr(committed_at, 1, 19) AND substr(committed_at, 11, 1) = 'T' AND CAST(substr(committed_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(committed_at, -1) = 'Z' OR substr(committed_at, -6) = '+00:00') AND instr(committed_at, char(0)) = 0)),
           authority_eligible INTEGER GENERATED ALWAYS AS (kind = 'live' AND result IN ('accepted', 'degraded')) STORED,
           version_eligible INTEGER GENERATED ALWAYS AS (result IN ('accepted', 'degraded')) STORED,
           CHECK ((kind IN ('live', 'replay') AND batch_id IS NULL) OR (kind IN ('reconciliation', 'backfill') AND batch_id IS NOT NULL)),
           UNIQUE (user_id, receipt_id),
           UNIQUE (user_id, receipt_id, kind),
           UNIQUE (user_id, receipt_id, kind, authority_eligible),
           UNIQUE (user_id, receipt_id, batch_id),
           UNIQUE (user_id, receipt_id, batch_id, version_eligible),
           FOREIGN KEY (user_id, import_id) REFERENCES imports(user_id, import_id),
           FOREIGN KEY (user_id, batch_id, kind) REFERENCES reconciliation_batches(user_id, batch_id, kind)
       )""",
    """CREATE TABLE receipt_artifacts (
           user_id TEXT NOT NULL,
           receipt_id TEXT NOT NULL,
           artifact_sha256 TEXT NOT NULL,
           purpose TEXT NOT NULL CHECK (purpose IN ('raw_payload', 'batch_source')),
           PRIMARY KEY (user_id, receipt_id, artifact_sha256, purpose),
           FOREIGN KEY (user_id, receipt_id) REFERENCES import_receipts(user_id, receipt_id),
           FOREIGN KEY (artifact_sha256) REFERENCES artifacts(artifact_sha256)
       )""",
    """CREATE TABLE receipt_errors (
           user_id TEXT NOT NULL,
           receipt_id TEXT NOT NULL,
           error_ordinal INTEGER NOT NULL CHECK (error_ordinal >= 0),
           code TEXT NOT NULL CHECK (length(code) > 0),
           metric TEXT,
           local_date TEXT CHECK (
               local_date IS NULL OR
               (length(local_date) = 10 AND date(local_date) = local_date)
           ),
           PRIMARY KEY (user_id, receipt_id, error_ordinal),
           FOREIGN KEY (user_id, receipt_id) REFERENCES import_receipts(user_id, receipt_id)
       )""",
    """CREATE TABLE reconciliation_batches (
           batch_id TEXT PRIMARY KEY,
           user_id TEXT NOT NULL,
           kind TEXT NOT NULL CHECK (kind IN ('reconciliation', 'backfill')),
           manifest_sha256 TEXT NOT NULL
               CHECK (length(CAST(manifest_sha256 AS BLOB)) = 64 AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
           scope_json TEXT NOT NULL CHECK (json_valid(scope_json)),
           status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'sealed', 'failed', 'abandoned')),
           approval_sha256 TEXT CHECK (
               approval_sha256 IS NULL OR
               (length(CAST(approval_sha256 AS BLOB)) = 64 AND approval_sha256 NOT GLOB '*[^0-9a-f]*')
           ),
           authority_sequence INTEGER CHECK (authority_sequence IS NULL OR authority_sequence > 0),
           sealed_at TEXT CHECK (sealed_at IS NULL OR (datetime(sealed_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', sealed_at) = substr(sealed_at, 1, 19) AND substr(sealed_at, 11, 1) = 'T' AND CAST(substr(sealed_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(sealed_at, -1) = 'Z' OR substr(sealed_at, -6) = '+00:00') AND instr(sealed_at, char(0)) = 0)),
           CHECK (
               (status = 'sealed' AND approval_sha256 IS NOT NULL AND authority_sequence IS NOT NULL AND sealed_at IS NOT NULL)
               OR
               (status <> 'sealed' AND authority_sequence IS NULL AND sealed_at IS NULL)
           ),
           UNIQUE (user_id, batch_id),
           UNIQUE (user_id, batch_id, manifest_sha256),
           UNIQUE (user_id, batch_id, kind),
           UNIQUE (user_id, batch_id, status),
           UNIQUE (user_id, batch_id, kind, status),
           UNIQUE (user_id, authority_sequence, batch_id),
           FOREIGN KEY (user_id) REFERENCES users(user_id),
           FOREIGN KEY (user_id, authority_sequence, batch_id)
               REFERENCES authority_events(user_id, authority_sequence, batch_id)
               DEFERRABLE INITIALLY DEFERRED
       )""",
    """CREATE TABLE batch_sources (
           user_id TEXT NOT NULL,
           batch_id TEXT NOT NULL,
           artifact_sha256 TEXT NOT NULL,
           source_ordinal INTEGER NOT NULL CHECK (source_ordinal >= 0),
           PRIMARY KEY (user_id, batch_id, artifact_sha256),
           UNIQUE (user_id, batch_id, source_ordinal),
           FOREIGN KEY (user_id, batch_id) REFERENCES reconciliation_batches(user_id, batch_id),
           FOREIGN KEY (artifact_sha256) REFERENCES artifacts(artifact_sha256)
       )""",
    """CREATE TABLE authority_events (
           user_id TEXT NOT NULL,
           authority_sequence INTEGER NOT NULL CHECK (authority_sequence > 0),
           live_receipt_id TEXT,
           live_receipt_kind TEXT,
           live_receipt_eligible INTEGER GENERATED ALWAYS AS (CASE WHEN live_receipt_id IS NOT NULL THEN 1 END) STORED,
           batch_id TEXT,
           batch_kind TEXT,
           batch_status TEXT GENERATED ALWAYS AS (CASE WHEN batch_id IS NOT NULL THEN 'sealed' END) STORED,
           created_at TEXT NOT NULL CHECK (datetime(created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', created_at) = substr(created_at, 1, 19) AND substr(created_at, 11, 1) = 'T' AND CAST(substr(created_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(created_at, -1) = 'Z' OR substr(created_at, -6) = '+00:00') AND instr(created_at, char(0)) = 0),
           PRIMARY KEY (user_id, authority_sequence),
           CHECK (
               (live_receipt_id IS NOT NULL AND live_receipt_kind = 'live' AND batch_id IS NULL AND batch_kind IS NULL)
               OR
               (live_receipt_id IS NULL AND live_receipt_kind IS NULL AND batch_id IS NOT NULL AND batch_kind IN ('reconciliation', 'backfill'))
           ),
           UNIQUE (user_id, live_receipt_id),
           UNIQUE (user_id, batch_id),
           UNIQUE (user_id, authority_sequence, live_receipt_id),
           UNIQUE (user_id, authority_sequence, batch_id),
           FOREIGN KEY (user_id) REFERENCES users(user_id),
           FOREIGN KEY (user_id, live_receipt_id, live_receipt_kind, live_receipt_eligible)
               REFERENCES import_receipts(user_id, receipt_id, kind, authority_eligible),
           FOREIGN KEY (user_id, batch_id, batch_kind, batch_status)
               REFERENCES reconciliation_batches(user_id, batch_id, kind, status)
       )""",
    """CREATE TABLE metric_versions (
           version_id TEXT PRIMARY KEY,
           user_id TEXT NOT NULL,
           receipt_id TEXT NOT NULL,
           batch_id TEXT,
           metric TEXT NOT NULL CHECK (length(metric) > 0),
           local_date TEXT NOT NULL CHECK (length(local_date) = 10 AND date(local_date) = local_date),
           version_kind TEXT NOT NULL CHECK (version_kind IN ('value', 'absence')),
           source_unit TEXT,
           canonical_unit TEXT,
           canonical_value TEXT,
           details_json TEXT CHECK (details_json IS NULL OR json_valid(details_json)),
           context_fingerprint TEXT NOT NULL
               CHECK (length(CAST(context_fingerprint AS BLOB)) = 64 AND context_fingerprint NOT GLOB '*[^0-9a-f]*'),
           completeness TEXT NOT NULL CHECK (completeness IN ('partial', 'complete', 'unknown')),
           validation_status TEXT NOT NULL CHECK (validation_status IN ('valid', 'pending', 'invalid', 'replay')),
           live_authority_sequence INTEGER,
           batch_authority_sequence INTEGER,
           receipt_eligible INTEGER GENERATED ALWAYS AS (CASE WHEN validation_status = 'valid' THEN 1 END) STORED,
           CHECK (
               (version_kind = 'value' AND source_unit IS NOT NULL AND canonical_unit IS NOT NULL AND canonical_value IS NOT NULL AND details_json IS NOT NULL)
               OR
               (version_kind = 'absence' AND source_unit IS NULL AND canonical_unit IS NULL AND canonical_value IS NULL AND details_json IS NULL)
           ),
           CHECK (
               (live_authority_sequence IS NOT NULL AND batch_authority_sequence IS NULL AND batch_id IS NULL AND validation_status = 'valid')
               OR
               (live_authority_sequence IS NULL AND batch_authority_sequence IS NOT NULL AND batch_id IS NOT NULL AND validation_status = 'valid')
               OR
               (live_authority_sequence IS NULL AND batch_authority_sequence IS NULL AND validation_status IN ('pending', 'invalid', 'replay'))
           ),
           UNIQUE (receipt_id, metric, local_date),
           UNIQUE (user_id, metric, local_date, version_id),
           UNIQUE (user_id, metric, local_date, version_id, validation_status),
           UNIQUE (user_id, batch_id, metric, local_date, version_id),
           UNIQUE (user_id, batch_id, metric, local_date, version_id, validation_status),
           FOREIGN KEY (user_id, receipt_id) REFERENCES import_receipts(user_id, receipt_id),
           FOREIGN KEY (user_id, receipt_id, batch_id) REFERENCES import_receipts(user_id, receipt_id, batch_id),
           FOREIGN KEY (user_id, receipt_id, batch_id, receipt_eligible) REFERENCES import_receipts(user_id, receipt_id, batch_id, version_eligible),
           FOREIGN KEY (user_id, live_authority_sequence, receipt_id)
               REFERENCES authority_events(user_id, authority_sequence, live_receipt_id),
           FOREIGN KEY (user_id, batch_authority_sequence, batch_id)
               REFERENCES authority_events(user_id, authority_sequence, batch_id)
       )""",
    """CREATE TABLE metric_current (
           user_id TEXT NOT NULL,
           metric TEXT NOT NULL,
           local_date TEXT NOT NULL,
           version_id TEXT NOT NULL,
           validation_status TEXT GENERATED ALWAYS AS ('valid') STORED,
           PRIMARY KEY (user_id, metric, local_date),
           FOREIGN KEY (user_id, metric, local_date, version_id, validation_status)
               REFERENCES metric_versions(user_id, metric, local_date, version_id, validation_status)
       )""",
    """CREATE TABLE batch_promotions (
           user_id TEXT NOT NULL,
           batch_id TEXT NOT NULL,
           metric TEXT NOT NULL,
           local_date TEXT NOT NULL,
           version_id TEXT NOT NULL,
           batch_status TEXT GENERATED ALWAYS AS ('sealed') STORED,
           validation_status TEXT GENERATED ALWAYS AS ('valid') STORED,
           PRIMARY KEY (user_id, batch_id, metric, local_date),
           FOREIGN KEY (user_id, batch_id, batch_status) REFERENCES reconciliation_batches(user_id, batch_id, status),
           FOREIGN KEY (user_id, batch_id, metric, local_date, version_id, validation_status)
               REFERENCES metric_versions(user_id, batch_id, metric, local_date, version_id, validation_status)
       )""",
    """CREATE TABLE semantic_evidence (
           evidence_id TEXT PRIMARY KEY,
           user_id TEXT NOT NULL,
           batch_id TEXT NOT NULL,
           manifest_sha256 TEXT NOT NULL CHECK (length(CAST(manifest_sha256 AS BLOB)) = 64 AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
           candidate_sha256 TEXT NOT NULL CHECK (length(CAST(candidate_sha256 AS BLOB)) = 64 AND candidate_sha256 NOT GLOB '*[^0-9a-f]*'),
           source_set_sha256 TEXT NOT NULL CHECK (length(CAST(source_set_sha256 AS BLOB)) = 64 AND source_set_sha256 NOT GLOB '*[^0-9a-f]*'),
           comparator_version TEXT NOT NULL,
           outcome TEXT NOT NULL CHECK (outcome IN ('passed', 'failed')),
           counts_json TEXT NOT NULL CHECK (json_valid(counts_json)),
           created_at TEXT NOT NULL CHECK (datetime(created_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', created_at) = substr(created_at, 1, 19) AND substr(created_at, 11, 1) = 'T' AND CAST(substr(created_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(created_at, -1) = 'Z' OR substr(created_at, -6) = '+00:00') AND instr(created_at, char(0)) = 0),
           UNIQUE (user_id, batch_id, manifest_sha256, candidate_sha256, source_set_sha256),
           FOREIGN KEY (user_id, batch_id, manifest_sha256) REFERENCES reconciliation_batches(user_id, batch_id, manifest_sha256)
       )""",
    """CREATE TABLE replay_operations (
           replay_id TEXT PRIMARY KEY,
           user_id TEXT NOT NULL,
           operation_key TEXT NOT NULL,
           import_id TEXT NOT NULL,
           receipt_id TEXT,
           evidence_json TEXT CHECK (evidence_json IS NULL OR json_valid(evidence_json)),
           completed_at TEXT CHECK (completed_at IS NULL OR (datetime(completed_at) IS NOT NULL AND strftime('%Y-%m-%dT%H:%M:%S', completed_at) = substr(completed_at, 1, 19) AND substr(completed_at, 11, 1) = 'T' AND CAST(substr(completed_at, 12, 2) AS INTEGER) BETWEEN 0 AND 23 AND (substr(completed_at, -1) = 'Z' OR substr(completed_at, -6) = '+00:00') AND instr(completed_at, char(0)) = 0)),
           UNIQUE (user_id, operation_key, import_id),
           FOREIGN KEY (user_id, import_id) REFERENCES imports(user_id, import_id),
           FOREIGN KEY (user_id, receipt_id) REFERENCES import_receipts(user_id, receipt_id)
       )""",
    """CREATE TABLE live_freshness (
           user_id TEXT PRIMARY KEY,
           latest_authenticated_receipt_id TEXT,
           latest_committed_receipt_id TEXT,
           latest_clean_receipt_id TEXT,
           latest_complete_local_date TEXT CHECK (
               latest_complete_local_date IS NULL OR
               (length(latest_complete_local_date) = 10 AND date(latest_complete_local_date) = latest_complete_local_date)
           ),
           FOREIGN KEY (user_id) REFERENCES users(user_id),
           FOREIGN KEY (user_id, latest_authenticated_receipt_id) REFERENCES import_receipts(user_id, receipt_id),
           FOREIGN KEY (user_id, latest_committed_receipt_id) REFERENCES import_receipts(user_id, receipt_id),
           FOREIGN KEY (user_id, latest_clean_receipt_id) REFERENCES import_receipts(user_id, receipt_id)
       )""",
    """CREATE TABLE dataset_state (
           singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
           user_id TEXT NOT NULL UNIQUE,
           state TEXT NOT NULL CHECK (state IN ('building', 'ready')),
           source_watermark TEXT,
           cutover_phase TEXT NOT NULL DEFAULT 'legacy'
               CHECK (cutover_phase IN ('legacy', 'candidate', 'cutover', 'accepted')),
           first_post_cutover_live_receipt_id TEXT,
           FOREIGN KEY (user_id) REFERENCES users(user_id),
           FOREIGN KEY (user_id, first_post_cutover_live_receipt_id)
               REFERENCES import_receipts(user_id, receipt_id)
       )""",
    "CREATE INDEX idx_receipts_import ON import_receipts(user_id, import_id)",
    "CREATE INDEX idx_receipts_status_time ON import_receipts(user_id, result, received_at)",
    "CREATE INDEX idx_versions_identity ON metric_versions(user_id, metric, local_date)",
    "CREATE INDEX idx_versions_receipt ON metric_versions(user_id, receipt_id)",
    "CREATE INDEX idx_batches_status ON reconciliation_batches(user_id, status)",
    "CREATE INDEX idx_batch_sources ON batch_sources(user_id, batch_id)",
    """CREATE TRIGGER metric_versions_context_unique BEFORE INSERT ON metric_versions
       WHEN EXISTS (
           SELECT 1 FROM metric_versions AS existing
           JOIN import_receipts AS old_receipt ON old_receipt.receipt_id = existing.receipt_id
           JOIN import_receipts AS new_receipt ON new_receipt.receipt_id = NEW.receipt_id
           WHERE existing.user_id = NEW.user_id AND old_receipt.import_id = new_receipt.import_id
             AND existing.metric = NEW.metric AND existing.local_date = NEW.local_date
             AND existing.context_fingerprint = NEW.context_fingerprint
       ) BEGIN SELECT RAISE(ABORT, 'duplicate metric context'); END""",
)

_LOCKS_GUARD = threading.Lock()
_WRITER_LOCKS: dict[Path, threading.Lock] = {}


def _require_private_directory(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError:
        raise RuntimeError("Candidate directory is unavailable") from None
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise RuntimeError("Candidate directory must be owned with mode 0700")


def _require_private_file(path: Path) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError:
        raise RuntimeError("Operational database is unavailable") from None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_nlink != 1
    ):
        raise RuntimeError("Operational path must be a private regular file")
    return metadata


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class _OperationalConnection(sqlite3.Connection):
    writer: OperationalWriterLock | None = None

    def close(self) -> None:
        writer = self.writer
        super().close()
        if writer is not None:
            writer._connection_closed()
            self.writer = None

    def __exit__(self, *args: object) -> bool:
        try:
            return bool(super().__exit__(*args))
        finally:
            self.close()


def connect_operational(
    path: Path, *, read_only: bool = True, writer: OperationalWriterLock | None = None
) -> sqlite3.Connection:
    before = _require_private_file(path)
    if not read_only:
        if writer is None or not writer.owns(path.parent):
            raise RuntimeError("Operational writer lock is required")
    mode = "ro" if read_only else "rw"
    connection = sqlite3.connect(
        f"{path.resolve().as_uri()}?mode={mode}",
        uri=True,
        timeout=BUSY_TIMEOUT_MS / 1000,
        factory=_OperationalConnection,
    )
    try:
        after = _require_private_file(path)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise RuntimeError("Operational database identity changed")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        connection.execute("PRAGMA synchronous=FULL")
        if not read_only:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.writer = writer
            writer._connection_opened()
        return connection
    except Exception:
        connection.close()
        raise


class OperationalWriterLock:
    def __init__(self, root: Path, *, blocking: bool = False):
        _require_private_directory(root)
        self.root = root
        self.path = root / "operational.writer.lock"
        self.blocking = blocking
        self._descriptor: int | None = None
        self._owner: int | None = None
        self._connections = 0
        with _LOCKS_GUARD:
            self._thread_lock = _WRITER_LOCKS.setdefault(root.resolve(), threading.Lock())

    def acquire(self) -> None:
        if self._descriptor is not None or not self._thread_lock.acquire(blocking=self.blocking):
            raise RuntimeError("Operational writer is already active")
        descriptor: int | None = None
        try:
            descriptor = os.open(
                self.path,
                os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600,
            )
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_nlink != 1
            ):
                raise RuntimeError("Writer lock must be a private regular file")
            try:
                flags = fcntl.LOCK_EX if self.blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
                fcntl.flock(descriptor, flags)
            except BlockingIOError:
                raise RuntimeError("Operational writer is already active") from None
            self._descriptor = descriptor
            self._owner = threading.get_ident()
        except OSError:
            if descriptor is not None:
                os.close(descriptor)
            self._thread_lock.release()
            raise RuntimeError("Writer lock must be a private regular file") from None
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            self._thread_lock.release()
            raise

    def release(self) -> None:
        if self._descriptor is None:
            return
        if self._owner != threading.get_ident():
            raise RuntimeError("Operational writer lock belongs to another thread")
        if self._connections:
            raise RuntimeError("Operational writer connection is still active")
        os.close(self._descriptor)
        self._descriptor = None
        self._owner = None
        self._thread_lock.release()

    def owns(self, root: Path) -> bool:
        return self._owner == threading.get_ident() and self.root.resolve() == root.resolve()

    def _connection_opened(self) -> None:
        self._connections += 1

    def _connection_closed(self) -> None:
        self._connections -= 1

    def __enter__(self) -> OperationalWriterLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def create_operational_database(
    root: Path,
    *,
    user_id: str,
    timezone: str = DATASET_TIMEZONE,
) -> Path:
    if not user_id or len(user_id) > 128:
        raise ValueError("Invalid operational owner")
    if timezone != DATASET_TIMEZONE:
        raise ValueError("Operational timezone must be Europe/Madrid")
    _require_private_directory(root)
    path = root / DATABASE_NAME
    created = False
    with OperationalWriterLock(root, blocking=True) as writer:
        if path.exists():
            validate_operational_database(path, user_id=user_id, timezone=timezone)
            return path
        try:
            descriptor = os.open(
                path,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600,
            )
            os.close(descriptor)
            created = True
            _sync_directory(root)
            with connect_operational(path, read_only=False, writer=writer) as db:
                db.execute("BEGIN IMMEDIATE")
                for statement in _DDL:
                    db.execute(statement)
                applied_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
                db.execute(
                    "INSERT INTO schema_migrations VALUES (?, ?)",
                    (SCHEMA_VERSION, applied_at),
                )
                db.execute(
                    "INSERT INTO users VALUES (?, ?, '1', 1)",
                    (user_id, timezone),
                )
                db.execute(
                    "INSERT INTO dataset_state (singleton, user_id, state) VALUES (1, ?, 'building')",
                    (user_id,),
                )
                db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                db.commit()
            _sync_directory(root)
        except Exception:
            if created:
                for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
                    candidate.unlink(missing_ok=True)
                _sync_directory(root)
            raise
    validate_operational_database(path, user_id=user_id, timezone=timezone)
    return path


def validate_operational_database(
    path: Path,
    *,
    user_id: str,
    timezone: str = DATASET_TIMEZONE,
    expected_state: str | None = None,
) -> None:
    try:
        with connect_operational(path, read_only=True) as db:
            if db.execute("PRAGMA application_id").fetchone() != (APPLICATION_ID,):
                raise RuntimeError("Operational schema identity is invalid")
            if db.execute("PRAGMA user_version").fetchone() != (SCHEMA_VERSION,):
                raise RuntimeError("Operational schema version is invalid")
            tables = {
                row[0]
                for row in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")
            }
            indexes = {
                row[0]
                for row in db.execute("SELECT name FROM sqlite_schema WHERE type='index'")
            }
            triggers = {row[0] for row in db.execute("SELECT name FROM sqlite_schema WHERE type='trigger'")}
            if not EXPECTED_TABLES <= tables or not EXPECTED_INDEXES <= indexes or not EXPECTED_TRIGGERS <= triggers:
                raise RuntimeError("Operational schema is incomplete")
            if db.execute("SELECT version FROM schema_migrations").fetchall() != [
                (SCHEMA_VERSION,)
            ]:
                raise RuntimeError("Operational schema migrations are invalid")
            owners = db.execute("SELECT user_id, timezone FROM users").fetchall()
            if owners != [(user_id, timezone)]:
                raise RuntimeError("Operational owner or timezone identity is invalid")
            if timezone != DATASET_TIMEZONE:
                raise RuntimeError("Operational timezone identity is invalid")
            states = db.execute("SELECT state FROM dataset_state").fetchall()
            if len(states) != 1 or (expected_state is not None and states != [(expected_state,)]):
                raise RuntimeError("Operational dataset state is invalid")
            if db.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
                raise RuntimeError("Operational journal mode is invalid")
            if db.execute("PRAGMA synchronous").fetchone() != (2,):
                raise RuntimeError("Operational synchronous mode is invalid")
            if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise RuntimeError("Operational foreign keys are invalid")
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise RuntimeError("Operational integrity check failed")
    except RuntimeError:
        raise
    except (OSError, sqlite3.Error):
        raise RuntimeError("Operational database is unavailable") from None
