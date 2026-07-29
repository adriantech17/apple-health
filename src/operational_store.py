from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import stat
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.storage_schema import OperationalWriterLock, connect_operational


FaultHook = Callable[[str], None]
_SAFE_CODE = re.compile(r"[a-z][a-z0-9_]{0,63}")
_SAFE_METRIC = re.compile(r"[a-z][a-z0-9_]{0,127}")


class StoreError(RuntimeError):
    """A privacy-safe operational persistence failure."""


@dataclass(frozen=True)
class ReceiptError:
    code: str
    metric: str | None = None
    local_date: str | None = None


@dataclass(frozen=True)
class ReceiptRecord:
    import_id: str
    receipt_id: str
    duplicate_import: bool
    artifact_retained: bool
    inserted_versions: int = 0
    authority_sequence: int | None = None


@dataclass(frozen=True)
class VersionCandidate:
    metric: str
    local_date: str
    version_kind: str
    source_unit: str | None
    canonical_unit: str | None
    canonical_value: str | None
    details_json: str | None
    context_fingerprint: str
    completeness: str
    validation_status: str = "valid"


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Receipt time must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_json(value: Mapping[str, Any]) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        raise ValueError("Invalid source metadata") from None


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _require_private_directory(path: Path) -> None:
    metadata = path.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise StoreError("Artifact directory verification failed")


def _make_private_directory(path: Path) -> None:
    if path.exists():
        _require_private_directory(path)
        return
    try:
        path.mkdir(mode=0o700)
        _sync_directory(path.parent)
    except (FileExistsError, OSError):
        raise StoreError("Artifact directory verification failed") from None
    _require_private_directory(path)


def _validate_error(error: ReceiptError) -> None:
    if not _SAFE_CODE.fullmatch(error.code):
        raise ValueError("Invalid receipt error")
    if error.metric is not None and not _SAFE_METRIC.fullmatch(error.metric):
        raise ValueError("Invalid receipt error")
    if error.local_date is not None:
        try:
            if date.fromisoformat(error.local_date).isoformat() != error.local_date:
                raise ValueError
        except ValueError:
            raise ValueError("Invalid receipt error") from None


def _validate_candidate(candidate: VersionCandidate, kind: str) -> None:
    if (
        not _SAFE_METRIC.fullmatch(candidate.metric)
        or not re.fullmatch(r"[0-9a-f]{64}", candidate.context_fingerprint)
        or candidate.completeness not in {"partial", "complete", "unknown"}
        or candidate.validation_status not in {"valid", "replay"}
        or (kind == "live" and candidate.validation_status != "valid")
        or (kind == "live" and candidate.version_kind == "absence")
        or (kind == "replay" and candidate.validation_status != "replay")
    ):
        raise ValueError("Invalid metric version")
    try:
        if date.fromisoformat(candidate.local_date).isoformat() != candidate.local_date:
            raise ValueError
        if candidate.details_json is not None:
            json.loads(candidate.details_json)
    except (ValueError, TypeError, json.JSONDecodeError):
        raise ValueError("Invalid metric version") from None
    values = (
        candidate.source_unit,
        candidate.canonical_unit,
        candidate.canonical_value,
        candidate.details_json,
    )
    if candidate.version_kind == "value" and any(value is None for value in values):
        raise ValueError("Invalid metric version")
    if candidate.version_kind == "absence" and any(value is not None for value in values):
        raise ValueError("Invalid metric version")
    if candidate.version_kind not in {"value", "absence"}:
        raise ValueError("Invalid metric version")


def _projection_winner(rows: Sequence[tuple[str, str, int]]) -> tuple[str, str | None]:
    complete = [row for row in rows if row[1] == "complete"]
    eligible = complete or rows
    if not eligible:
        return "missing", None
    highest = eligible[0][2]
    winners = [row for row in eligible if row[2] == highest]
    return ("selected", winners[0][0]) if len(winners) == 1 else ("conflict", None)


class OperationalStore:
    def __init__(
        self,
        database: Path,
        *,
        user_id: str,
        fault: FaultHook | None = None,
    ):
        self.database = database
        self.root = database.parent
        self.user_id = user_id
        self._fault = fault or (lambda _: None)

    def _artifact_path(self, digest: str) -> tuple[Path, str]:
        relative = Path("raw-v2") / "sha256" / digest[:2] / f"{digest}.json.gz"
        return self.root / relative, relative.as_posix()

    def _prepare_artifact_parent(self, final: Path) -> None:
        current = self.root
        _require_private_directory(current)
        for part in final.parent.relative_to(self.root).parts:
            current /= part
            _make_private_directory(current)

    def _read_private_artifact(self, path: Path) -> bytes:
        try:
            metadata = path.lstat()
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_nlink != 1
            ):
                raise StoreError
            with gzip.open(path, "rb") as source:
                return source.read()
        except (OSError, EOFError, gzip.BadGzipFile, StoreError):
            raise StoreError("Stored artifact verification failed") from None

    def _verify_artifact(self, path: Path, digest: str, expected_bytes: int | None = None) -> None:
        restored = self._read_private_artifact(path)
        if (
            (expected_bytes is not None and len(restored) != expected_bytes)
            or hashlib.sha256(restored).hexdigest() != digest
        ):
            raise StoreError("Stored artifact verification failed")

    def _publish_artifact(self, body: bytes, digest: str) -> tuple[str, bool]:
        final, relative = self._artifact_path(digest)
        self._prepare_artifact_parent(final)
        if os.path.lexists(final):
            self._verify_artifact(final, digest, len(body))
            return relative, False

        staging = final.with_name(f".{uuid.uuid4().hex}.staging")
        descriptor: int | None = None
        published = False
        try:
            descriptor = os.open(
                staging,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600,
            )
            with os.fdopen(os.dup(descriptor), "wb") as raw:
                with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as output:
                    output.write(body)
            self._fault("after_stage_write")
            os.fsync(descriptor)
            self._fault("after_stage_sync")
            os.close(descriptor)
            descriptor = None
            os.rename(staging, final)
            published = True
            self._fault("after_rename")
            _sync_directory(final.parent)
            self._fault("after_parent_sync")
            return relative, True
        except OSError:
            raise StoreError("Artifact publication failed") from None
        finally:
            try:
                if descriptor is not None:
                    os.close(descriptor)
                if not published:
                    staging.unlink(missing_ok=True)
            except OSError:
                raise StoreError("Artifact publication failed") from None

    def record_receipt(
        self,
        body: bytes,
        *,
        receipt_id: str,
        kind: str,
        parser_version: str,
        contract_version: str,
        source_metadata: Mapping[str, Any],
        result: str,
        received_at: datetime,
        contract_valid: bool,
        errors: Sequence[ReceiptError] = (),
        versions: Sequence[VersionCandidate] = (),
        latest_complete_local_date: str | None = None,
    ) -> ReceiptRecord:
        if kind not in {"live", "replay"} or result not in {
            "accepted",
            "degraded",
            "rejected",
        } or (versions and result == "rejected"):
            raise ValueError("Invalid receipt context")
        if not all(isinstance(value, str) and value for value in (receipt_id, parser_version, contract_version)):
            raise ValueError("Invalid receipt context")
        for error in errors:
            _validate_error(error)
        for version in versions:
            _validate_candidate(version, kind)
        if latest_complete_local_date is not None:
            try:
                if date.fromisoformat(latest_complete_local_date).isoformat() != latest_complete_local_date:
                    raise ValueError
            except ValueError:
                raise ValueError("Invalid freshness date") from None

        candidates: dict[tuple[str, str], VersionCandidate] = {}
        conflicts: set[tuple[str, str]] = set()
        for version in versions:
            identity = (version.metric, version.local_date)
            previous = candidates.get(identity)
            if previous is not None and previous != version:
                conflicts.add(identity)
            else:
                candidates[identity] = version
        for identity in conflicts:
            candidates.pop(identity, None)
        receipt_errors = list(errors)
        receipt_errors.extend(
            ReceiptError("unresolved_conflict", metric, local_date)
            for metric, local_date in sorted(conflicts)
        )

        received_text = _timestamp(received_at)
        metadata_json = _canonical_json(source_metadata)
        digest = hashlib.sha256(body).hexdigest()
        retain_raw = kind == "live" and (result in {"accepted", "degraded"} or contract_valid)
        relative_path: str | None = None
        writer = OperationalWriterLock(self.root, blocking=True)
        writer.acquire()
        try:
            if retain_raw:
                relative_path, _ = self._publish_artifact(body, digest)
            with connect_operational(self.database, read_only=False, writer=writer) as db:
                db.execute("BEGIN IMMEDIATE")
                existing = db.execute(
                    "SELECT import_id, payload_bytes FROM imports WHERE user_id=? AND payload_sha256=?",
                    (self.user_id, digest),
                ).fetchone()
                if existing is not None and existing[1] != len(body):
                    raise StoreError("Logical import verification failed")
                import_id = existing[0] if existing else str(uuid.uuid4())
                if existing is None:
                    db.execute(
                        "INSERT INTO imports VALUES (?, ?, ?, ?, ?)",
                        (import_id, self.user_id, digest, len(body), received_text),
                    )
                db.execute(
                    """INSERT INTO import_receipts (
                           receipt_id, user_id, import_id, kind, parser_version,
                           contract_version, source_metadata_json, result,
                           received_at, committed_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        receipt_id,
                        self.user_id,
                        import_id,
                        kind,
                        parser_version,
                        contract_version,
                        metadata_json,
                        result,
                        received_text,
                        received_text if result in {"accepted", "degraded"} else None,
                    ),
                )
                new_versions: list[VersionCandidate] = []
                for version in candidates.values():
                    duplicate = db.execute(
                        """SELECT 1
                           FROM metric_versions AS version
                           JOIN import_receipts AS receipt
                             ON receipt.user_id=version.user_id
                            AND receipt.receipt_id=version.receipt_id
                           WHERE receipt.import_id=? AND version.metric=?
                              AND version.local_date=? AND version.context_fingerprint=?
                              AND receipt.kind=?""",
                        (
                            import_id,
                            version.metric,
                            version.local_date,
                            version.context_fingerprint,
                            kind,
                        ),
                    ).fetchone()
                    if duplicate is None:
                        new_versions.append(version)
                authority_sequence: int | None = None
                if kind == "live" and new_versions:
                    authority_sequence = db.execute(
                        "SELECT next_authority_sequence FROM users WHERE user_id=?",
                        (self.user_id,),
                    ).fetchone()[0]
                    db.execute(
                        "UPDATE users SET next_authority_sequence=? WHERE user_id=?",
                        (authority_sequence + 1, self.user_id),
                    )
                    db.execute(
                        """INSERT INTO authority_events
                           (user_id, authority_sequence, live_receipt_id,
                            live_receipt_kind, created_at)
                           VALUES (?, ?, ?, 'live', ?)""",
                        (self.user_id, authority_sequence, receipt_id, received_text),
                    )
                    self._fault("after_authority")
                if relative_path is not None:
                    db.execute(
                        "INSERT OR IGNORE INTO artifacts VALUES (?, 'live_raw', ?, ?)",
                        (digest, relative_path, len(body)),
                    )
                    db.execute(
                        "INSERT INTO receipt_artifacts VALUES (?, ?, ?, 'raw_payload')",
                        (self.user_id, receipt_id, digest),
                    )
                db.executemany(
                    "INSERT INTO receipt_errors VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        (self.user_id, receipt_id, ordinal, item.code, item.metric, item.local_date)
                        for ordinal, item in enumerate(receipt_errors)
                    ),
                )
                for version in new_versions:
                    db.execute(
                        """INSERT INTO metric_versions
                           (version_id, user_id, receipt_id, metric, local_date,
                            version_kind, source_unit, canonical_unit, canonical_value,
                            details_json, context_fingerprint, completeness,
                            validation_status, live_authority_sequence)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            str(uuid.uuid4()),
                            self.user_id,
                            receipt_id,
                            version.metric,
                            version.local_date,
                            version.version_kind,
                            version.source_unit,
                            version.canonical_unit,
                            version.canonical_value,
                            version.details_json,
                            version.context_fingerprint,
                            version.completeness,
                            version.validation_status,
                            authority_sequence,
                        ),
                    )
                if new_versions:
                    self._fault("after_versions")
                if authority_sequence is not None:
                    self._apply_projection(
                        db,
                        {(version.metric, version.local_date) for version in new_versions},
                    )
                    self._fault("after_projection")
                if kind == "live":
                    db.execute(
                        "INSERT OR IGNORE INTO live_freshness (user_id) VALUES (?)",
                        (self.user_id,),
                    )
                    assignments = ["latest_authenticated_receipt_id=?"]
                    values: list[str] = [receipt_id]
                    if result in {"accepted", "degraded"}:
                        assignments.append("latest_committed_receipt_id=?")
                        values.append(receipt_id)
                    if result == "accepted":
                        assignments.append("latest_clean_receipt_id=?")
                        values.append(receipt_id)
                    if latest_complete_local_date is not None:
                        assignments.append(
                            "latest_complete_local_date=MAX(COALESCE(latest_complete_local_date,''),?)"
                        )
                        values.append(latest_complete_local_date)
                    db.execute(
                        f"UPDATE live_freshness SET {','.join(assignments)} WHERE user_id=?",
                        (*values, self.user_id),
                    )
                    db.execute(
                        """UPDATE dataset_state
                           SET first_post_cutover_live_receipt_id=?
                           WHERE user_id=? AND cutover_phase IN ('cutover','accepted')
                             AND first_post_cutover_live_receipt_id IS NULL""",
                        (receipt_id, self.user_id),
                    )
                    self._fault("after_freshness")
                self._fault("before_sqlite_commit")
                db.commit()
            _sync_directory(self.root)
        finally:
            writer.release()
        return ReceiptRecord(
            import_id,
            receipt_id,
            existing is not None,
            retain_raw,
            len(new_versions),
            authority_sequence,
        )

    def _apply_projection(self, db: Any, identities: set[tuple[str, str]]) -> None:
        for metric, local_date in sorted(identities):
            rows = db.execute(
                """SELECT version.version_id, version.completeness,
                          COALESCE(version.live_authority_sequence,
                                   version.batch_authority_sequence) AS sequence
                   FROM metric_versions AS version
                   WHERE version.user_id=? AND version.metric=? AND version.local_date=?
                     AND version.validation_status='valid'
                     AND (
                         version.live_authority_sequence IS NOT NULL
                         OR EXISTS (
                             SELECT 1 FROM batch_promotions AS promotion
                             WHERE promotion.user_id=version.user_id
                               AND promotion.batch_id=version.batch_id
                               AND promotion.metric=version.metric
                               AND promotion.local_date=version.local_date
                               AND promotion.version_id=version.version_id
                         )
                     )
                   ORDER BY sequence DESC, version.version_id""",
                (self.user_id, metric, local_date),
            ).fetchall()
            outcome, version_id = _projection_winner(rows)
            if outcome == "missing":
                db.execute(
                    "DELETE FROM metric_current WHERE user_id=? AND metric=? AND local_date=?",
                    (self.user_id, metric, local_date),
                )
                continue
            if outcome == "conflict":
                continue
            db.execute(
                """INSERT INTO metric_current (user_id, metric, local_date, version_id)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT (user_id, metric, local_date)
                   DO UPDATE SET version_id=excluded.version_id""",
                (self.user_id, metric, local_date, version_id),
            )

    def rebuild_current(self) -> None:
        with OperationalWriterLock(self.root, blocking=True) as writer:
            with connect_operational(self.database, read_only=False, writer=writer) as db:
                db.execute("BEGIN IMMEDIATE")
                identities = {
                    (row[0], row[1])
                    for row in db.execute(
                        "SELECT DISTINCT metric, local_date FROM metric_versions WHERE user_id=?",
                        (self.user_id,),
                    )
                }
                db.execute("DELETE FROM metric_current WHERE user_id=?", (self.user_id,))
                self._apply_projection(db, identities)
                db.commit()
        _sync_directory(self.root)

    def quarantine_orphans(self) -> int:
        with OperationalWriterLock(self.root, blocking=True):
            raw_root = self.root / "raw-v2" / "sha256"
            if not raw_root.exists():
                return 0
            with connect_operational(self.database) as db:
                referenced = {row[0] for row in db.execute("SELECT relative_path FROM artifacts")}
            quarantine = self.root / "quarantine"
            moved = 0
            for artifact in raw_root.glob("*/*.json.gz"):
                relative = artifact.relative_to(self.root).as_posix()
                if relative in referenced:
                    continue
                digest = artifact.name.removesuffix(".json.gz")
                if not re.fullmatch(r"[0-9a-f]{64}", digest):
                    continue
                try:
                    self._verify_artifact(artifact, digest)
                except StoreError:
                    continue
                _make_private_directory(quarantine)
                destination = quarantine / artifact.name
                if os.path.lexists(destination):
                    raise StoreError("Orphan quarantine verification failed")
                os.rename(artifact, destination)
                _sync_directory(artifact.parent)
                _sync_directory(quarantine)
                moved += 1
            return moved
