from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.metric_contracts import MetricContractError, normalize_metric, parse_json_decimal
from src.operational_store import ReceiptError, VersionCandidate
from src.storage_schema import OperationalWriterLock, connect_operational


_DIGEST = re.compile(r"[0-9a-f]{64}")
_SAFE_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}")
_SAFE_METRIC = re.compile(r"[a-z][a-z0-9_]{0,127}")
FaultHook = Callable[[str], None]


class ReconciliationError(RuntimeError):
    """A stable, privacy-safe reconciliation failure."""


@dataclass(frozen=True)
class ReconciliationResult:
    resumed: bool
    sources: int
    versions: int
    errors: int


@dataclass(frozen=True)
class _Manifest:
    batch_id: str
    kind: str
    owner: str
    timezone: str
    importer_version: str
    expected_counts: Mapping[str, int]
    required_evidence: tuple[str, ...]
    scope: Mapping[str, Any]
    generation_context: Mapping[str, Any]
    identities: Mapping[tuple[str, str], str]
    sources: tuple[tuple[str, str], ...]


def _canonical_json(value: object) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    except (TypeError, ValueError):
        raise ReconciliationError("Manifest shape invalid") from None


def _private_file(path: Path) -> bytes:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_nlink != 1
        ):
            raise OSError
        with os.fdopen(os.dup(descriptor), "rb") as source:
            return source.read()
    except OSError:
        raise ReconciliationError("Private input verification failed") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _require_private_directory(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError:
        raise ReconciliationError("Private output verification failed") from None
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise ReconciliationError("Private output verification failed")


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _private_directory(root: Path, relative: Path) -> Path:
    current = root
    _require_private_directory(current)
    for part in relative.parts:
        current /= part
        if current.exists():
            _require_private_directory(current)
            continue
        try:
            current.mkdir(mode=0o700)
            _sync_directory(current.parent)
        except OSError:
            raise ReconciliationError("Private output verification failed") from None
        _require_private_directory(current)
    return current


def _inside_git_worktree(root: Path) -> bool:
    current = root.resolve()
    return any(os.path.lexists(candidate / ".git") for candidate in (current, *current.parents))


def _verify_output_root(root: Path) -> None:
    _require_private_directory(root)
    if _inside_git_worktree(root):
        raise ReconciliationError("Private output cannot be inside a Git worktree")


def discard_staging(root: Path, candidate: Path) -> None:
    try:
        resolved_root = root.resolve(strict=True)
        resolved_candidate = candidate.resolve(strict=True)
        relative = resolved_candidate.relative_to(resolved_root)
        metadata = resolved_candidate.lstat()
        if candidate.parent.resolve(strict=True) / candidate.name != resolved_candidate:
            raise ValueError
    except (ValueError, OSError):
        raise ReconciliationError("Cleanup target is not disposable staging") from None
    if (
        not relative.parts
        or relative.parts[0] != "batch-sources"
        or not resolved_candidate.name.startswith(".")
        or not resolved_candidate.name.endswith(".staging")
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
    ):
        raise ReconciliationError("Cleanup target is not disposable staging")
    try:
        resolved_candidate.unlink()
        _sync_directory(resolved_candidate.parent)
    except OSError:
        raise ReconciliationError("Disposable staging cleanup failed") from None


def _publish(root: Path, relative: Path, content: bytes) -> None:
    parent = _private_directory(root, relative.parent)
    final = root / relative
    if os.path.lexists(final):
        if _private_file(final) != content:
            raise ReconciliationError("Stored artifact verification failed")
        return
    staging = parent / f".{uuid.uuid4().hex}.staging"
    descriptor: int | None = None
    published = False
    try:
        descriptor = os.open(
            staging,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
        )
        remaining = memoryview(content)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError
            remaining = remaining[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.rename(staging, final)
        published = True
        _sync_directory(parent)
    except OSError:
        raise ReconciliationError("Artifact publication failed") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if not published and os.path.lexists(staging):
            discard_staging(root, staging)


def _parse_manifest(content: bytes, owner: str, timezone: str) -> _Manifest:
    try:
        parsed = json.loads(content, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ReconciliationError("Manifest JSON invalid") from None
    if _canonical_json(parsed) != content:
        raise ReconciliationError("Manifest is not canonical")
    required = {
        "batch_id",
        "expected_counts",
        "generation_context",
        "identities",
        "importer_version",
        "kind",
        "owner",
        "required_evidence",
        "schema_version",
        "scope",
        "sources",
        "timezone",
    }
    if not isinstance(parsed, dict) or set(parsed) != required or parsed.get("schema_version") != 1:
        raise ReconciliationError("Manifest shape invalid")
    if parsed.get("owner") != owner or parsed.get("timezone") != timezone:
        raise ReconciliationError("Manifest identity invalid")
    batch_id = parsed.get("batch_id")
    kind = parsed.get("kind")
    importer = parsed.get("importer_version")
    context = parsed.get("generation_context")
    if (
        not isinstance(batch_id, str)
        or not _SAFE_ID.fullmatch(batch_id)
        or kind not in {"reconciliation", "backfill"}
        or not isinstance(importer, str)
        or not importer
        or not isinstance(context, dict)
    ):
        raise ReconciliationError("Manifest shape invalid")
    scope = parsed.get("scope")
    if not isinstance(scope, dict) or set(scope) != {"start_date", "end_date", "metrics"}:
        raise ReconciliationError("Manifest scope invalid")
    try:
        start = date.fromisoformat(scope["start_date"])
        end = date.fromisoformat(scope["end_date"])
        metrics = scope["metrics"]
        if (
            start > end
            or not isinstance(metrics, list)
            or not metrics
            or len(metrics) != len(set(metrics))
            or any(not isinstance(item, str) or not _SAFE_METRIC.fullmatch(item) for item in metrics)
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise ReconciliationError("Manifest scope invalid") from None
    identities: dict[tuple[str, str], str] = {}
    raw_identities = parsed.get("identities")
    if not isinstance(raw_identities, list) or not raw_identities:
        raise ReconciliationError("Manifest scope invalid")
    for item in raw_identities:
        try:
            if not isinstance(item, dict) or set(item) != {"metric", "local_date", "state"}:
                raise ValueError
            metric = item["metric"]
            local_date = item["local_date"]
            identity_date = date.fromisoformat(local_date)
            identity = (metric, local_date)
            if (
                metric not in metrics
                or not start <= identity_date <= end
                or item["state"] not in {"value", "absence"}
                or identity in identities
            ):
                raise ValueError
            identities[identity] = item["state"]
        except (KeyError, TypeError, ValueError):
            raise ReconciliationError("Manifest scope invalid") from None
    raw_sources = parsed.get("sources")
    sources: list[tuple[str, str]] = []
    source_names: set[str] = set()
    source_digests: set[str] = set()
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ReconciliationError("Manifest sources invalid")
    for item in raw_sources:
        if not isinstance(item, dict) or set(item) != {"name", "sha256"}:
            raise ReconciliationError("Manifest sources invalid")
        name, digest = item.get("name"), item.get("sha256")
        if (
            not isinstance(name, str)
            or not _SAFE_ID.fullmatch(name)
            or not isinstance(digest, str)
            or not _DIGEST.fullmatch(digest)
            or name in source_names
            or digest in source_digests
        ):
            raise ReconciliationError("Manifest sources invalid")
        sources.append((name, digest))
        source_names.add(name)
        source_digests.add(digest)
    expected_counts = parsed.get("expected_counts")
    required_evidence = parsed.get("required_evidence")
    if (
        not isinstance(expected_counts, dict)
        or set(expected_counts) != {"identities", "sources"}
        or any(isinstance(value, bool) or not isinstance(value, int) for value in expected_counts.values())
        or expected_counts != {"identities": len(identities), "sources": len(sources)}
        or not isinstance(required_evidence, list)
        or "semantic_comparison" not in required_evidence
        or len(required_evidence) != len(set(required_evidence))
        or any(not isinstance(item, str) or not _SAFE_ID.fullmatch(item) for item in required_evidence)
    ):
        raise ReconciliationError("Manifest shape invalid")
    return _Manifest(
        batch_id,
        kind,
        owner,
        timezone,
        importer,
        expected_counts,
        tuple(required_evidence),
        scope,
        context,
        identities,
        tuple(sources),
    )


def _local_date(row: Mapping[str, Any], timezone: str) -> str:
    raw = row.get("date") or row.get("startDate") or row.get("sleepStart")
    if not isinstance(raw, str):
        raise ValueError
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return date.fromisoformat(raw).isoformat()
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError
    return parsed.astimezone(ZoneInfo(timezone)).date().isoformat()


def _source_candidates(
    content: bytes, manifest: _Manifest, source_ordinal: int
) -> tuple[list[tuple[int, VersionCandidate]], list[tuple[int, ReceiptError]]]:
    candidates: list[tuple[int, VersionCandidate]] = []
    errors: list[tuple[int, ReceiptError]] = []
    try:
        payload = parse_json_decimal(content)
        groups = payload.get("data", {}).get("metrics") if isinstance(payload, Mapping) else None
        if not isinstance(groups, list):
            raise MetricContractError("invalid_json")
    except MetricContractError as error:
        return [], [(source_ordinal, ReceiptError(error.code))]
    for group in groups:
        metric = group.get("name") if isinstance(group, Mapping) else None
        unit = group.get("units") if isinstance(group, Mapping) else None
        rows = group.get("data") if isinstance(group, Mapping) else None
        if not isinstance(metric, str) or not isinstance(rows, list):
            errors.append((source_ordinal, ReceiptError("invalid_metric_group")))
            continue
        for row in rows:
            local_date: str | None = None
            try:
                if not isinstance(row, Mapping):
                    raise ValueError
                local_date = _local_date(row, manifest.timezone)
                normalized = normalize_metric(
                    metric,
                    unit,
                    row,
                    completeness="complete",
                    provenance={"batch": manifest.batch_id, "local_date": local_date},
                    kind=manifest.kind,
                    parser_version="1",
                    contract_version="1",
                    trusted_batch_context={
                        "batch_id": manifest.batch_id,
                        "generation_context": manifest.generation_context,
                    },
                )
                candidates.append(
                    (
                        source_ordinal,
                        VersionCandidate(
                            normalized.metric,
                            local_date,
                            "value",
                            normalized.source_unit,
                            normalized.canonical_unit,
                            normalized.canonical_value,
                            normalized.details_json,
                            normalized.context_fingerprint,
                            "complete",
                            "pending",
                        ),
                    )
                )
            except MetricContractError as error:
                safe_metric = metric if _SAFE_METRIC.fullmatch(metric) else None
                errors.append((source_ordinal, ReceiptError(error.code, safe_metric, local_date)))
            except (TypeError, ValueError):
                safe_metric = metric if _SAFE_METRIC.fullmatch(metric) else None
                errors.append((source_ordinal, ReceiptError("invalid_date", safe_metric, local_date)))
    return candidates, errors


def _validated_candidates(
    manifest: _Manifest, contents: list[bytes]
) -> tuple[list[tuple[int, VersionCandidate]], list[tuple[int, ReceiptError]]]:
    candidates: list[tuple[int, VersionCandidate]] = []
    errors: list[tuple[int, ReceiptError]] = []
    for ordinal, content in enumerate(contents):
        source_candidates, source_errors = _source_candidates(content, manifest, ordinal)
        candidates.extend(source_candidates)
        errors.extend(source_errors)
    accepted: dict[tuple[str, str], list[tuple[int, VersionCandidate]]] = {}
    conflicts: set[tuple[str, str]] = set()
    for ordinal, candidate in candidates:
        identity = (candidate.metric, candidate.local_date)
        state = manifest.identities.get(identity)
        if state is None:
            errors.append((ordinal, ReceiptError("undeclared_identity", *identity)))
        elif state != "value":
            conflicts.add(identity)
        elif identity in accepted:
            if accepted[identity][0][1] == candidate:
                accepted[identity].append((ordinal, candidate))
            else:
                conflicts.add(identity)
        else:
            accepted[identity] = [(ordinal, candidate)]
    for identity in conflicts:
        accepted.pop(identity, None)
        errors.append((0, ReceiptError("unresolved_conflict", *identity)))
    for identity, state in manifest.identities.items():
        if state == "value" and identity not in accepted:
            errors.append((0, ReceiptError("missing_identity", *identity)))
        elif state == "absence" and identity not in conflicts:
            fingerprint = hashlib.sha256(
                _canonical_json(
                    {
                        "batch": manifest.batch_id,
                        "completeness": "complete",
                        "identity": identity,
                        "kind": manifest.kind,
                        "state": "absence",
                    }
                )
            ).hexdigest()
            accepted[identity] = [
                (
                    0,
                    VersionCandidate(
                        identity[0], identity[1], "absence", None, None, None, None,
                        fingerprint, "complete", "pending",
                    ),
                )
            ]
    return [candidate for occurrences in accepted.values() for candidate in occurrences], errors


def _resume_result(db: Any, manifest: _Manifest) -> ReconciliationResult:
    sources = db.execute(
        "SELECT COUNT(*) FROM batch_sources WHERE user_id=? AND batch_id=?",
        (manifest.owner, manifest.batch_id),
    ).fetchone()[0]
    versions = db.execute(
        "SELECT COUNT(*) FROM metric_versions WHERE user_id=? AND batch_id=?",
        (manifest.owner, manifest.batch_id),
    ).fetchone()[0]
    errors = db.execute(
        """SELECT COUNT(*) FROM receipt_errors AS error
           JOIN import_receipts AS receipt ON receipt.user_id=error.user_id AND receipt.receipt_id=error.receipt_id
           WHERE receipt.user_id=? AND receipt.batch_id=?""",
        (manifest.owner, manifest.batch_id),
    ).fetchone()[0]
    return ReconciliationResult(True, sources, versions, errors)


def stage_reconciliation(
    database: Path,
    manifest_path: Path,
    source_root: Path,
    *,
    fault: FaultHook | None = None,
) -> ReconciliationResult:
    root = database.parent
    _verify_output_root(root)
    _require_private_directory(source_root)
    manifest_bytes = _private_file(manifest_path)
    with connect_operational(database) as db:
        owner, timezone = db.execute("SELECT user_id,timezone FROM users").fetchone()
    manifest = _parse_manifest(manifest_bytes, owner, timezone)
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    contents: list[bytes] = []
    for name, digest in manifest.sources:
        content = _private_file(source_root / name)
        if hashlib.sha256(content).hexdigest() != digest:
            raise ReconciliationError("Source verification failed")
        contents.append(content)
    candidates, errors = _validated_candidates(manifest, contents)
    hook = fault or (lambda _: None)
    with OperationalWriterLock(root, blocking=True) as writer:
        with connect_operational(database, read_only=False, writer=writer) as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT manifest_sha256,status FROM reconciliation_batches WHERE user_id=? AND batch_id=?",
                (owner, manifest.batch_id),
            ).fetchone()
            if existing is not None and existing[0] != manifest_digest:
                raise ReconciliationError("Batch manifest mismatch")
            if existing is not None and existing[1] != "pending":
                raise ReconciliationError("Batch is not pending")
            manifest_relative = Path("manifests") / f"{manifest.batch_id}.json"
            _publish(root, manifest_relative, manifest_bytes)
            source_relatives: list[Path] = []
            for (_, digest), content in zip(manifest.sources, contents, strict=True):
                relative = Path("batch-sources") / "sha256" / digest[:2] / f"{digest}.json"
                _publish(root, relative, content)
                source_relatives.append(relative)
            hook("after_source_publication")
            if existing is not None:
                result = _resume_result(db, manifest)
                db.rollback()
                return result
            scope_json = _canonical_json(
                {
                    "generation_context": manifest.generation_context,
                    "expected_counts": manifest.expected_counts,
                    "identities": [
                        {"local_date": identity[1], "metric": identity[0], "state": state}
                        for identity, state in sorted(manifest.identities.items())
                    ],
                    "importer_version": manifest.importer_version,
                    "required_evidence": manifest.required_evidence,
                    "scope": manifest.scope,
                }
            ).decode().rstrip("\n")
            db.execute(
                "INSERT INTO reconciliation_batches VALUES (?,?,?,?,?,'pending',NULL,NULL,NULL)",
                (manifest.batch_id, owner, manifest.kind, manifest_digest, scope_json),
            )
            receipt_ids: list[str] = []
            for ordinal, ((_, digest), content, relative) in enumerate(
                zip(manifest.sources, contents, source_relatives, strict=True)
            ):
                receipt_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{owner}:{manifest.batch_id}:{ordinal}"))
                receipt_ids.append(receipt_id)
                prior_import = db.execute(
                    "SELECT import_id,payload_bytes FROM imports WHERE user_id=? AND payload_sha256=?",
                    (owner, digest),
                ).fetchone()
                if prior_import is None:
                    import_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{owner}:{digest}"))
                    db.execute(
                        "INSERT INTO imports VALUES (?,?,?,?, '1970-01-01T00:00:00Z')",
                        (import_id, owner, digest, len(content)),
                    )
                elif prior_import[1] == len(content):
                    import_id = prior_import[0]
                else:
                    raise ReconciliationError("Logical import verification failed")
                db.execute(
                    """INSERT INTO artifacts VALUES (?, 'batch_source', ?, ?)
                       ON CONFLICT(artifact_sha256) DO UPDATE SET
                         kind=excluded.kind, relative_path=excluded.relative_path,
                         artifact_bytes=excluded.artifact_bytes""",
                    (digest, relative.as_posix(), len(content)),
                )
                db.execute(
                    """INSERT INTO import_receipts
                       (receipt_id,user_id,import_id,batch_id,kind,parser_version,contract_version,
                        source_metadata_json,result,received_at,committed_at)
                       VALUES (?,?,?,?,?,'1','1',?,'pending','1970-01-01T00:00:00Z',NULL)""",
                    (receipt_id, owner, import_id, manifest.batch_id, manifest.kind, json.dumps({"source_ordinal": ordinal})),
                )
                db.execute(
                    "INSERT INTO batch_sources VALUES (?,?,?,?)",
                    (owner, manifest.batch_id, digest, ordinal),
                )
                db.execute(
                    "INSERT INTO receipt_artifacts VALUES (?,?,?,'batch_source')",
                    (owner, receipt_id, digest),
                )
            for ordinal, error in errors:
                error_ordinal = db.execute(
                    "SELECT COUNT(*) FROM receipt_errors WHERE user_id=? AND receipt_id=?",
                    (owner, receipt_ids[ordinal]),
                ).fetchone()[0]
                db.execute(
                    "INSERT INTO receipt_errors VALUES (?,?,?,?,?,?)",
                    (owner, receipt_ids[ordinal], error_ordinal, error.code, error.metric, error.local_date),
                )
            for ordinal, candidate in candidates:
                version_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{owner}:{manifest.batch_id}:{ordinal}:{candidate.metric}:{candidate.local_date}",
                    )
                )
                db.execute(
                    """INSERT INTO metric_versions
                       (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,
                        source_unit,canonical_unit,canonical_value,details_json,context_fingerprint,
                        completeness,validation_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'pending')""",
                    (
                        version_id, owner, receipt_ids[ordinal], manifest.batch_id,
                        candidate.metric, candidate.local_date, candidate.version_kind,
                        candidate.source_unit, candidate.canonical_unit, candidate.canonical_value,
                        candidate.details_json, candidate.context_fingerprint, candidate.completeness,
                    ),
                )
            hook("before_sqlite_commit")
            db.commit()
    _sync_directory(root)
    return ReconciliationResult(False, len(contents), len(candidates), len(errors))
