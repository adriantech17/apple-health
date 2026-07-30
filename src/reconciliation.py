from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.metric_contracts import MetricContractError, normalize_metric, parse_json_decimal
from src.operational_store import ReceiptError, VersionCandidate, apply_projection
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
class ReconciliationEvidenceBinding:
    manifest_sha256: str
    source_set_sha256: str
    counts_json: str


@dataclass(frozen=True)
class SealResult:
    resumed: bool
    authority_sequence: int
    identities: int
    versions: int


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


def _evidence_binding(db: Any, owner: str, batch_id: str) -> ReconciliationEvidenceBinding:
    batch = db.execute(
        "SELECT manifest_sha256 FROM reconciliation_batches WHERE user_id=? AND batch_id=?",
        (owner, batch_id),
    ).fetchone()
    if batch is None:
        raise ReconciliationError("Batch does not exist")
    sources = db.execute(
        """SELECT source_ordinal,artifact_sha256 FROM batch_sources
           WHERE user_id=? AND batch_id=? ORDER BY source_ordinal""",
        (owner, batch_id),
    ).fetchall()
    receipts = db.execute(
        """SELECT receipt_id,import_id,kind,result,source_metadata_json
           FROM import_receipts WHERE user_id=? AND batch_id=? ORDER BY receipt_id""",
        (owner, batch_id),
    ).fetchall()
    versions = db.execute(
        """SELECT version_id,receipt_id,metric,local_date,version_kind,source_unit,
                  canonical_unit,canonical_value,details_json,context_fingerprint,
                  completeness,validation_status,live_authority_sequence,batch_authority_sequence
           FROM metric_versions WHERE user_id=? AND batch_id=?
           ORDER BY metric,local_date,receipt_id,version_id""",
        (owner, batch_id),
    ).fetchall()
    errors = db.execute(
        """SELECT error.receipt_id,error.error_ordinal,error.code,error.metric,error.local_date
           FROM receipt_errors AS error
           JOIN import_receipts AS receipt
             ON receipt.user_id=error.user_id AND receipt.receipt_id=error.receipt_id
           WHERE receipt.user_id=? AND receipt.batch_id=?
           ORDER BY error.receipt_id,error.error_ordinal""",
        (owner, batch_id),
    ).fetchall()
    links = db.execute(
        """SELECT link.receipt_id,link.artifact_sha256,link.purpose
           FROM receipt_artifacts AS link
           JOIN import_receipts AS receipt
             ON receipt.user_id=link.user_id AND receipt.receipt_id=link.receipt_id
           WHERE receipt.user_id=? AND receipt.batch_id=?
           ORDER BY link.receipt_id,link.artifact_sha256,link.purpose""",
        (owner, batch_id),
    ).fetchall()
    snapshot = {
        "errors": errors,
        "links": links,
        "receipts": receipts,
        "sources": sources,
        "versions": versions,
    }
    snapshot_digest = hashlib.sha256(_canonical_json(snapshot)).hexdigest()
    source_set_digest = hashlib.sha256(
        _canonical_json([digest for _, digest in sources])
    ).hexdigest()
    counts = {
        "errors": len(errors),
        "identities": len({(row[2], row[3]) for row in versions}),
        "receipts": len(receipts),
        "snapshot_sha256": snapshot_digest,
        "sources": len(sources),
        "versions": len(versions),
    }
    return ReconciliationEvidenceBinding(
        batch[0], source_set_digest, _canonical_json(counts).decode().rstrip("\n")
    )


def reconciliation_evidence_binding(
    database: Path, batch_id: str
) -> ReconciliationEvidenceBinding:
    with connect_operational(database) as db:
        owner = db.execute("SELECT user_id FROM users").fetchone()[0]
        return _evidence_binding(db, owner, batch_id)


def _verify_batch_for_seal(
    db: Any,
    root: Path,
    owner: str,
    timezone: str,
    batch_id: str,
    approval_manifest_sha256: str,
    *,
    retained_only: bool = False,
) -> tuple[_Manifest, ReconciliationEvidenceBinding]:
    batch = db.execute(
        """SELECT kind,manifest_sha256,status FROM reconciliation_batches
           WHERE user_id=? AND batch_id=?""",
        (owner, batch_id),
    ).fetchone()
    if batch is None:
        raise ReconciliationError("Batch does not exist")
    _, manifest_sha256, status = batch
    if status != ("sealed" if retained_only else "pending"):
        raise ReconciliationError("Batch is not pending")
    if not _DIGEST.fullmatch(approval_manifest_sha256) or approval_manifest_sha256 != manifest_sha256:
        raise ReconciliationError("Approval manifest mismatch")
    manifest_bytes = _private_file(root / "manifests" / f"{batch_id}.json")
    if hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256:
        raise ReconciliationError("Retained manifest verification failed")
    manifest = _parse_manifest(manifest_bytes, owner, timezone)
    if manifest.batch_id != batch_id or manifest.kind != batch[0]:
        raise ReconciliationError("Retained manifest verification failed")

    source_rows = db.execute(
        """SELECT source.source_ordinal,source.artifact_sha256,artifact.kind,
                  artifact.relative_path,artifact.artifact_bytes
           FROM batch_sources AS source
           JOIN artifacts AS artifact ON artifact.artifact_sha256=source.artifact_sha256
           WHERE source.user_id=? AND source.batch_id=? ORDER BY source.source_ordinal""",
        (owner, batch_id),
    ).fetchall()
    if [(row[0], row[1]) for row in source_rows] != [
        (ordinal, digest) for ordinal, (_, digest) in enumerate(manifest.sources)
    ]:
        raise ReconciliationError("Batch lineage is incomplete")
    for ordinal, digest, kind, relative_path, expected_bytes in source_rows:
        expected_relative = Path("batch-sources") / "sha256" / digest[:2] / f"{digest}.json"
        if kind != "batch_source" or relative_path != expected_relative.as_posix():
            raise ReconciliationError("Batch lineage is incomplete")
        content = _private_file(root / expected_relative)
        if len(content) != expected_bytes or hashlib.sha256(content).hexdigest() != digest:
            raise ReconciliationError("Retained source verification failed")
    if retained_only:
        return manifest, _evidence_binding(db, owner, batch_id)

    receipts = db.execute(
        """SELECT receipt_id,kind,result,source_metadata_json FROM import_receipts
           WHERE user_id=? AND batch_id=? ORDER BY receipt_id""",
        (owner, batch_id),
    ).fetchall()
    receipt_sources: dict[int, str] = {}
    for receipt_id, kind, result, metadata_json in receipts:
        try:
            metadata = json.loads(metadata_json)
            ordinal = metadata["source_ordinal"]
        except (json.JSONDecodeError, KeyError, TypeError):
            raise ReconciliationError("Batch lineage is incomplete") from None
        if (
            kind != manifest.kind
            or result != "pending"
            or isinstance(ordinal, bool)
            or not isinstance(ordinal, int)
            or ordinal in receipt_sources
            or not 0 <= ordinal < len(manifest.sources)
        ):
            raise ReconciliationError("Batch lineage is incomplete")
        linked = db.execute(
            """SELECT artifact_sha256,purpose FROM receipt_artifacts
               WHERE user_id=? AND receipt_id=?""",
            (owner, receipt_id),
        ).fetchall()
        if linked != [(manifest.sources[ordinal][1], "batch_source")]:
            raise ReconciliationError("Batch lineage is incomplete")
        receipt_sources[ordinal] = receipt_id
    if set(receipt_sources) != set(range(len(manifest.sources))):
        raise ReconciliationError("Batch lineage is incomplete")
    errors = db.execute(
        """SELECT COUNT(*) FROM receipt_errors AS error
           JOIN import_receipts AS receipt
             ON receipt.user_id=error.user_id AND receipt.receipt_id=error.receipt_id
           WHERE receipt.user_id=? AND receipt.batch_id=?""",
        (owner, batch_id),
    ).fetchone()[0]
    if errors:
        raise ReconciliationError("Batch has blocking validation errors")

    versions = db.execute(
        """SELECT version_id,receipt_id,metric,local_date,version_kind,source_unit,
                  canonical_unit,canonical_value,details_json,context_fingerprint,
                  completeness,validation_status,live_authority_sequence,batch_authority_sequence
           FROM metric_versions WHERE user_id=? AND batch_id=?
           ORDER BY metric,local_date,receipt_id,version_id""",
        (owner, batch_id),
    ).fetchall()
    grouped: dict[tuple[str, str], list[tuple[Any, ...]]] = {}
    for row in versions:
        if row[1] not in receipt_sources.values() or row[11:] != ("pending", None, None):
            raise ReconciliationError("Batch lineage is incomplete")
        grouped.setdefault((row[2], row[3]), []).append(row)
    if set(grouped) != set(manifest.identities):
        raise ReconciliationError("Batch identity population mismatch")
    for identity, rows in grouped.items():
        expected_kind = manifest.identities[identity]
        content = {row[4:11] for row in rows}
        if len(content) != 1 or rows[0][4] != expected_kind:
            raise ReconciliationError("Batch identity population mismatch")

    binding = _evidence_binding(db, owner, batch_id)
    evidence = db.execute(
        """SELECT source_set_sha256,counts_json FROM semantic_evidence
           WHERE user_id=? AND batch_id=? AND manifest_sha256=? AND outcome='passed'""",
        (owner, batch_id, manifest_sha256),
    ).fetchall()
    if not evidence:
        raise ReconciliationError("Successful semantic evidence is missing")
    if (binding.source_set_sha256, binding.counts_json) not in evidence:
        raise ReconciliationError("Semantic evidence is stale")
    return manifest, binding


def seal_reconciliation(
    database: Path,
    batch_id: str,
    approval_manifest_sha256: str,
    *,
    sealed_at: datetime | None = None,
    fault: FaultHook | None = None,
) -> SealResult:
    root = database.parent
    _verify_output_root(root)
    hook = fault or (lambda _: None)
    seal_time = sealed_at or datetime.now(UTC)
    if seal_time.tzinfo is None or seal_time.utcoffset() is None:
        raise ValueError("Seal time must be timezone-aware")
    sealed_text = seal_time.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    with OperationalWriterLock(root, blocking=True) as writer:
        with connect_operational(database, read_only=False, writer=writer) as db:
            db.execute("BEGIN IMMEDIATE")
            owner, timezone = db.execute("SELECT user_id,timezone FROM users").fetchone()
            existing = db.execute(
                """SELECT status,manifest_sha256,approval_sha256,authority_sequence
                   FROM reconciliation_batches WHERE user_id=? AND batch_id=?""",
                (owner, batch_id),
            ).fetchone()
            if existing is None:
                raise ReconciliationError("Batch does not exist")
            if existing[0] == "sealed":
                if (
                    approval_manifest_sha256 != existing[1]
                    or existing[2] != approval_manifest_sha256
                    or existing[3] is None
                ):
                    raise ReconciliationError("Approval manifest mismatch")
                manifest, binding = _verify_batch_for_seal(
                    db,
                    root,
                    owner,
                    timezone,
                    batch_id,
                    approval_manifest_sha256,
                    retained_only=True,
                )
                identities, receipts, invalid_receipts, versions, invalid_versions, evidence = db.execute(
                    """SELECT
                         (SELECT COUNT(*) FROM batch_promotions WHERE user_id=? AND batch_id=?),
                         (SELECT COUNT(*) FROM import_receipts WHERE user_id=? AND batch_id=?),
                         (SELECT COUNT(*) FROM import_receipts WHERE user_id=? AND batch_id=?
                            AND (result<>'accepted' OR committed_at IS NULL)),
                         (SELECT COUNT(*) FROM metric_versions WHERE user_id=? AND batch_id=?),
                         (SELECT COUNT(*) FROM metric_versions WHERE user_id=? AND batch_id=?
                            AND (validation_status<>'valid' OR batch_authority_sequence<>?)),
                         (SELECT COUNT(*) FROM semantic_evidence WHERE user_id=? AND batch_id=?
                            AND manifest_sha256=? AND source_set_sha256=? AND outcome='passed')""",
                    (
                        owner, batch_id, owner, batch_id, owner, batch_id,
                        owner, batch_id, owner, batch_id, existing[3], owner, batch_id,
                        existing[1], binding.source_set_sha256,
                    ),
                ).fetchone()
                if (
                    identities != len(manifest.identities)
                    or receipts != len(manifest.sources)
                    or invalid_receipts
                    or versions < identities
                    or invalid_versions
                    or not evidence
                ):
                    raise ReconciliationError("Sealed batch lineage is incomplete")
                db.rollback()
                return SealResult(True, existing[3], identities, versions)
            manifest, _ = _verify_batch_for_seal(
                db, root, owner, timezone, batch_id, approval_manifest_sha256
            )
            authority_sequence = db.execute(
                "SELECT next_authority_sequence FROM users WHERE user_id=?", (owner,)
            ).fetchone()[0]
            db.execute(
                """UPDATE reconciliation_batches
                   SET status='sealed',approval_sha256=?,authority_sequence=?,sealed_at=?
                   WHERE user_id=? AND batch_id=? AND status='pending'""",
                (
                    approval_manifest_sha256,
                    authority_sequence,
                    sealed_text,
                    owner,
                    batch_id,
                ),
            )
            db.execute(
                """INSERT INTO authority_events
                   (user_id,authority_sequence,batch_id,batch_kind,created_at)
                   VALUES (?,?,?,?,?)""",
                (owner, authority_sequence, batch_id, manifest.kind, sealed_text),
            )
            db.execute(
                "UPDATE users SET next_authority_sequence=? WHERE user_id=?",
                (authority_sequence + 1, owner),
            )
            hook("after_authority")
            db.execute(
                """UPDATE import_receipts SET result='accepted',committed_at=?
                   WHERE user_id=? AND batch_id=? AND result='pending'""",
                (sealed_text, owner, batch_id),
            )
            db.execute(
                """UPDATE metric_versions
                   SET validation_status='valid',batch_authority_sequence=?
                   WHERE user_id=? AND batch_id=? AND validation_status='pending'""",
                (authority_sequence, owner, batch_id),
            )
            hook("after_activation")
            promoted = db.execute(
                """SELECT metric,local_date,MIN(version_id),COUNT(*)
                   FROM metric_versions WHERE user_id=? AND batch_id=?
                   GROUP BY metric,local_date ORDER BY metric,local_date""",
                (owner, batch_id),
            ).fetchall()
            db.executemany(
                """INSERT INTO batch_promotions
                   (user_id,batch_id,metric,local_date,version_id) VALUES (?,?,?,?,?)""",
                (
                    (owner, batch_id, metric, local_date, version_id)
                    for metric, local_date, version_id, _ in promoted
                ),
            )
            hook("after_promotions")
            apply_projection(db, owner, {(row[0], row[1]) for row in promoted})
            hook("after_projection")
            hook("before_sqlite_commit")
            db.commit()
    _sync_directory(root)
    return SealResult(
        False,
        authority_sequence,
        len(promoted),
        sum(row[3] for row in promoted),
    )


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
