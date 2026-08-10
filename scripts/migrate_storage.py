from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.maintenance import MaintenanceGate
from src.metric_contracts import METRIC_CONTRACTS, canonical_json
from src.operational_store import apply_projection
from src.reconciliation import (
    _canonical_json as _canonical,
    _private_file as _private_bytes,
    _publish as _publish_artifact,
    _require_private_directory as _private_directory,
    _sync_directory,
    reconciliation_evidence_binding,
    stage_reconciliation,
)
from src.storage_schema import (
    OperationalWriterLock,
    connect_operational,
    create_operational_database,
)


FaultHook = Callable[[str], None]
_STATE_VERSION = 1


class MigrationError(RuntimeError):
    """A stable migration failure that does not expose private input."""

@dataclass(frozen=True)
class CandidateResult:
    resumed: bool
    phase: str
    source_files: int
    evidence_gaps: int
    source_watermark: str
    candidate_sha256: str

@dataclass(frozen=True)
class ComparisonResult:
    passed: bool
    differences: int
    expected_legacy_corrections: int
    candidate_sha256: str
    source_set_sha256: str
    checks: Mapping[str, bool]

def _make_directory(path: Path) -> None:
    if path.exists():
        _private_directory(path)
        return
    try:
        path.mkdir(mode=0o700)
        _sync_directory(path.parent)
    except OSError:
        raise MigrationError("Private migration directory is unavailable") from None
    _private_directory(path)

def _publish(path: Path, content: bytes) -> None:
    _make_directory(path.parent)
    _publish_artifact(path.parent, Path(path.name), content)

def _source_inventory(root: Path) -> tuple[list[dict[str, object]], str]:
    _private_directory(root)
    inventory: list[dict[str, object]] = []
    try:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if relative.endswith("-shm"):
                continue
            metadata = path.lstat()
            if stat.S_ISDIR(metadata.st_mode):
                _private_directory(path)
                continue
            content = _private_bytes(path)
            inventory.append(
                {"bytes": len(content), "path": relative, "sha256": hashlib.sha256(content).hexdigest()}
            )
    except MigrationError:
        raise
    except OSError:
        raise MigrationError("Legacy source inventory failed") from None
    return inventory, hashlib.sha256(_canonical(inventory)).hexdigest()

def _sqlite_backup(source: Path, destination: Path) -> bytes:
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.staging")
    try:
        with sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True) as source_db:
            with sqlite3.connect(temporary) as destination_db:
                source_db.backup(destination_db)
        temporary.chmod(0o600)
        content = _private_bytes(temporary)
        _publish(destination, content)
        return content
    except (OSError, sqlite3.Error):
        raise MigrationError("SQLite online snapshot failed") from None
    finally:
        temporary.unlink(missing_ok=True)

def _copy_evidence(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    _private_directory(source)
    _make_directory(destination)
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            _make_directory(destination / relative)
        else:
            _publish(destination / relative, _private_bytes(path))

def _read_canonical(path: Path) -> tuple[Mapping[str, Any], bytes]:
    content = _private_bytes(path)
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise MigrationError("Migration input is invalid") from None
    if not isinstance(value, Mapping) or _canonical(value) != content:
        raise MigrationError("Migration input is invalid")
    return value, content

def _state_path(candidate: Path) -> Path:
    return candidate / "migration" / "candidate-state.json"

def _write_state(candidate: Path, state: Mapping[str, Any]) -> None:
    path = _state_path(candidate)
    _make_directory(path.parent)
    content = _canonical(state)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.staging")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
        )
        try:
            remaining = memoryview(content)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError
                remaining = remaining[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        _sync_directory(path.parent)
    except OSError:
        raise MigrationError("Candidate state publication failed") from None
    finally:
        temporary.unlink(missing_ok=True)

def _version_values(version: Mapping[str, Any]) -> tuple[Any, ...]:
    required = {
        "canonical_unit", "canonical_value", "completeness", "context_fingerprint",
        "details", "local_date", "metric", "source_unit", "version_kind",
    }
    if set(version) != required or version["version_kind"] not in {"value", "absence"}:
        raise MigrationError("Reconstruction input is invalid")
    details = json.dumps(version["details"], sort_keys=True, separators=(",", ":"))
    if version["version_kind"] == "absence":
        values = (None, None, None, None)
    else:
        values = (
            version["source_unit"], version["canonical_unit"], version["canonical_value"], details,
        )
    return (
        version["metric"], version["local_date"], version["version_kind"], *values,
        version["context_fingerprint"], version["completeness"],
    )

def _insert_import(db: sqlite3.Connection, owner: str, receipt: Mapping[str, Any]) -> None:
    db.execute(
        "INSERT INTO imports VALUES (?,?,?,?,?)",
        (
            receipt["import_id"], owner, receipt["payload_sha256"], receipt["payload_bytes"],
            receipt["received_at"],
        ),
    )

def _insert_version(
    db: sqlite3.Connection,
    owner: str,
    receipt_id: str,
    version: Mapping[str, Any],
    *,
    sequence: int,
    batch_id: str | None = None,
) -> tuple[str, str, str]:
    values = _version_values(version)
    version_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"migration:{owner}:{receipt_id}:{values[0]}:{values[1]}",
        )
    )
    db.execute(
        """INSERT INTO metric_versions
           (version_id,user_id,receipt_id,batch_id,metric,local_date,version_kind,
            source_unit,canonical_unit,canonical_value,details_json,context_fingerprint,
            completeness,validation_status,live_authority_sequence,batch_authority_sequence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'valid',?,?)""",
        (
            version_id, owner, receipt_id, batch_id, *values,
            sequence if batch_id is None else None,
            sequence if batch_id is not None else None,
        ),
    )
    return values[0], values[1], version_id

def _reconstruct(db: sqlite3.Connection, plan: Mapping[str, Any], fault: FaultHook) -> None:
    required = {
        "backfill_batches", "evidence_gaps", "expected_legacy_corrections", "freshness",
        "live_receipts", "owner", "schema_version", "timezone",
    }
    if set(plan) != required or plan["schema_version"] != 1:
        raise MigrationError("Reconstruction input is invalid")
    owner = plan["owner"]
    identities: set[tuple[str, str]] = set()
    sequences: list[int] = []
    for receipt in plan["live_receipts"]:
        _insert_import(db, owner, receipt)
        sequence = receipt["authority_sequence"]
        sequences.append(sequence)
        db.execute(
            """INSERT INTO import_receipts
               (receipt_id,user_id,import_id,kind,parser_version,contract_version,
                source_metadata_json,result,received_at,committed_at)
               VALUES (?,?,?,'live','1','1','{}',?,?,?)""",
            (
                receipt["receipt_id"], owner, receipt["import_id"], receipt["result"],
                receipt["received_at"],
                receipt["received_at"] if receipt["result"] in {"accepted", "degraded"} else None,
            ),
        )
        db.execute(
            "INSERT INTO authority_events (user_id,authority_sequence,live_receipt_id,live_receipt_kind,created_at) VALUES (?,?,?,'live',?)",
            (owner, sequence, receipt["receipt_id"], receipt["received_at"]),
        )
        for version in receipt["versions"]:
            metric, local_date, _ = _insert_version(
                db, owner, receipt["receipt_id"], version, sequence=sequence
            )
            identities.add((metric, local_date))
    for batch in plan["backfill_batches"]:
        receipt = batch["receipt"]
        sequence = batch["authority_sequence"]
        sequences.append(sequence)
        _insert_import(db, owner, receipt)
        db.execute(
            """INSERT INTO reconciliation_batches
               (batch_id,user_id,kind,manifest_sha256,scope_json,status,approval_sha256,
                authority_sequence,sealed_at)
               VALUES (?,?,'backfill',?,'{}','sealed',?,?,?)""",
            (
                batch["batch_id"], owner, batch["manifest_sha256"], batch["manifest_sha256"],
                sequence, batch["sealed_at"],
            ),
        )
        db.execute(
            """INSERT INTO import_receipts
               (receipt_id,user_id,import_id,batch_id,kind,parser_version,contract_version,
                source_metadata_json,result,received_at,committed_at)
               VALUES (?,?,?,?,'backfill','1','1','{}','accepted',?,?)""",
            (
                receipt["receipt_id"], owner, receipt["import_id"], batch["batch_id"],
                receipt["received_at"], batch["sealed_at"],
            ),
        )
        db.execute(
            "INSERT INTO authority_events (user_id,authority_sequence,batch_id,batch_kind,created_at) VALUES (?,?,?,'backfill',?)",
            (owner, sequence, batch["batch_id"], batch["sealed_at"]),
        )
        for version in batch["versions"]:
            metric, local_date, version_id = _insert_version(
                db,
                owner,
                receipt["receipt_id"],
                version,
                sequence=sequence,
                batch_id=batch["batch_id"],
            )
            db.execute(
                "INSERT INTO batch_promotions VALUES (?,?,?,?,?)",
                (owner, batch["batch_id"], metric, local_date, version_id),
            )
            identities.add((metric, local_date))
    apply_projection(db, owner, identities)
    freshness = plan["freshness"]
    db.execute(
        "INSERT INTO live_freshness VALUES (?,?,?,?,?)",
        (
            owner,
            freshness["latest_authenticated_receipt_id"],
            freshness["latest_committed_receipt_id"],
            freshness["latest_clean_receipt_id"],
            freshness["latest_complete_local_date"],
        ),
    )
    db.execute(
        "UPDATE users SET next_authority_sequence=? WHERE user_id=?",
        ((max(sequences) + 1) if sequences else 1, owner),
    )
    fault("before_reconstruction_commit")

def _candidate_hash(database: Path) -> str:
    temporary = database.parent / "migration" / ".candidate-hash.sqlite3"
    temporary.unlink(missing_ok=True)
    try:
        with connect_operational(database) as source:
            with sqlite3.connect(temporary) as destination:
                source.backup(destination)
        temporary.chmod(0o600)
        return hashlib.sha256(_private_bytes(temporary)).hexdigest()
    finally:
        temporary.unlink(missing_ok=True)

def _decimal(value: object) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise MigrationError("Reference normalization failed") from None
    if not number.is_finite():
        raise MigrationError("Reference normalization failed")
    text = format(number, "f") if number else "0"
    text = text.rstrip("0").rstrip(".") if "." in text else text
    return text or "0"

def _reference_json(value: object) -> str:
    if isinstance(value, Decimal):
        return _decimal(value)
    if isinstance(value, Mapping):
        return "{" + ",".join(f"{json.dumps(key)}:{_reference_json(value[key])}" for key in sorted(value)) + "}"
    return json.dumps(value, separators=(",", ":"))

def _reference_value(metric: str, unit: str, row: Mapping[str, Any]) -> tuple[str, str, str]:
    key = next((name for name in ("qty", "Avg", "totalSleep", "asleep") if name in row), None)
    if key is None:
        raise MigrationError("Reference normalization failed")
    conversions = {
        ("active_energy", "kJ"): ("1", "4.184", "kcal"),
        ("basal_energy_burned", "kJ"): ("1", "4.184", "kcal"),
        ("walking_running_distance", "m"): (".001", "1", "km"),
        ("walking_speed", "m/s"): ("3.6", "1", "km/h"),
        ("walking_step_length", "m"): ("100", "1", "cm"),
        ("stair_speed_up", "km/h"): ("1", "3.6", "m/s"),
        ("stair_speed_down", "km/h"): ("1", "3.6", "m/s"),
        ("sleep_analysis", "min"): ("1", "60", "h"),
    }
    aliases = {"km/hr": "km/h", "kcal/hr·kg": "kcal/h/kg", "mL/min·kg": "mL/kg/min"}
    canonical_source = aliases.get(unit, unit)
    multiplier, divisor, canonical_unit = conversions.get((metric, canonical_source), ("1", "1", canonical_source))
    def convert(raw: object) -> Decimal:
        with localcontext() as context:
            context.prec = 50
            return Decimal(_decimal(raw)) * Decimal(multiplier) / Decimal(divisor)
    value = convert(row[key])
    if unit == "count/min" and metric in {"resting_heart_rate", "walking_heart_rate_average", "heart_rate", "cardio_recovery"}:
        canonical_unit = "bpm"
    if metric == "sleep_analysis" and unit == "hr":
        canonical_unit = "h"
    elif metric == "blood_oxygen_saturation" and unit == "%" and value <= 1:
        value *= 100
    details: Mapping[str, Any] = {}
    if metric == "heart_rate":
        details = {"maximum": convert(row.get("Max")), "minimum": convert(row.get("Min"))}
    elif metric == "sleep_analysis":
        details = {name: convert(row[source]) for name, source in (("awake", "awake"), ("core", "core"), ("deep", "deep"), ("rem", "rem"))}
        details |= {"sleep_end": row["sleepEnd"], "sleep_start": row["sleepStart"]}
        details |= {name: convert(row[source]) for name, source in (("asleep", "asleep"), ("in_bed", "inBed")) if source in row}
        details |= {name: row[source] for name, source in (("in_bed_start", "inBedStart"), ("in_bed_end", "inBedEnd")) if source in row}
    return _decimal(value), canonical_unit, _reference_json(details)

def _reference_fingerprint(
    metric: str, source_unit: str, value: str, details_json: str, manifest: Mapping[str, Any]
) -> str:
    contract = METRIC_CONTRACTS[metric]
    content = {
        "canonical_unit": contract.canonical_unit,
        "canonical_value": value,
        "completeness": "complete",
        "contract_version": "1",
        "details": json.loads(details_json, parse_float=Decimal, parse_int=Decimal),
        "kind": manifest["kind"],
        "metric_contract": {
            "accepted_source_units": sorted(contract.accepted_source_units),
            "canonical_unit": contract.canonical_unit,
            "daily_shape": contract.daily_shape,
            "identity_forms": sorted(contract.identity_forms),
            "name": contract.name,
        },
        "parser_version": "1",
        "source_unit": source_unit,
        "trusted_batch_context": {
            "batch_id": manifest["batch_id"],
            "generation_context": manifest["generation_context"],
        },
    }
    return hashlib.sha256(canonical_json(content).encode()).hexdigest()

def _reference_local_date(row: Mapping[str, Any], timezone: str) -> str:
    raw = row.get("date") or row.get("startDate") or row.get("sleepStart")
    if not isinstance(raw, str):
        raise MigrationError("Reference normalization failed")
    try:
        if len(raw) == 10:
            return date.fromisoformat(raw).isoformat()
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(ZoneInfo(timezone)).date().isoformat()
    except ValueError:
        raise MigrationError("Reference normalization failed") from None

def _reference_snapshot(
    manifest: Mapping[str, Any], source_root: Path, plan: Mapping[str, Any]
) -> Mapping[str, Any]:
    versions: list[tuple[Any, ...]] = []
    for source in manifest["sources"]:
        try:
            payload = json.loads(_private_bytes(source_root / source["name"]), parse_float=Decimal, parse_int=Decimal)
            groups = payload["data"]["metrics"]
        except (KeyError, TypeError, json.JSONDecodeError):
            raise MigrationError("Reference normalization failed") from None
        for group in groups:
            for row in group["data"]:
                value, unit, details = _reference_value(group["name"], group["units"], row)
                fingerprint = _reference_fingerprint(
                    group["name"], group["units"], value, details, manifest
                )
                versions.append(
                    (
                        group["name"], _reference_local_date(row, plan["timezone"]), "value",
                        group["units"], unit, value,
                        details, fingerprint, "complete", "pending", None, "reconciliation",
                        "1970-01-01T00:00:00Z", manifest["batch_id"],
                    )
                )
    current: dict[tuple[str, str], tuple[tuple[bool, int], tuple[Any, ...]]] = {}
    for population, kind in ((plan["live_receipts"], "live"), (plan["backfill_batches"], "backfill")):
        for item in population:
            receipt = item if kind == "live" else item["receipt"]
            for version in item["versions"]:
                values = _version_values(version)
                row = (*values, "valid", item["authority_sequence"], kind,
                       receipt["received_at"], None if kind == "live" else item["batch_id"])
                versions.append(row)
                identity = row[:2]
                selected = ((values[8] == "complete", item["authority_sequence"]), row[:8] + (item["authority_sequence"],))
                if identity not in current or selected[0] > current[identity][0]:
                    current[identity] = selected
    batches = [(manifest["batch_id"], "reconciliation", None, None)] + [
        (item["batch_id"], "backfill", item["authority_sequence"], item["sealed_at"])
        for item in plan["backfill_batches"]
    ]
    return {
        "batches": sorted(batches),
        "current": sorted(item[1] for item in current.values()),
        "freshness": tuple(plan["freshness"].values()),
        "gaps": sorted(item["code"] for item in plan["evidence_gaps"]),
        "imports": sorted([(item["sha256"], len(_private_bytes(source_root / item["name"]))) for item in manifest["sources"]] + [(item["payload_sha256"], item["payload_bytes"]) for item in plan["live_receipts"]] + [(item["receipt"]["payload_sha256"], item["receipt"]["payload_bytes"]) for item in plan["backfill_batches"]]),
        "live": sorted((item["receipt_id"], item["result"], item["received_at"]) for item in plan["live_receipts"]),
        "owner": (plan["owner"], plan["timezone"]),
        "versions": sorted(versions),
    }

def _actual_snapshot(database: Path) -> Mapping[str, Any]:
    state, _ = _read_canonical(_state_path(database.parent))
    with connect_operational(database) as db:
        versions = db.execute(
            """SELECT v.metric,v.local_date,v.version_kind,v.source_unit,v.canonical_unit,
                      v.canonical_value,v.details_json,v.context_fingerprint,v.completeness,v.validation_status,
                      COALESCE(v.live_authority_sequence,v.batch_authority_sequence),r.kind,
                      r.received_at,v.batch_id FROM metric_versions v JOIN import_receipts r
                      ON r.user_id=v.user_id AND r.receipt_id=v.receipt_id ORDER BY 1,2,11,12"""
        ).fetchall()
        current = db.execute(
            """SELECT v.metric,v.local_date,v.version_kind,v.source_unit,v.canonical_unit,
                      v.canonical_value,v.details_json,v.context_fingerprint,
                      COALESCE(v.live_authority_sequence,v.batch_authority_sequence)
               FROM metric_current c JOIN metric_versions v ON v.version_id=c.version_id ORDER BY 1,2"""
        ).fetchall()
        return {
            "batches": db.execute("SELECT batch_id,kind,authority_sequence,sealed_at FROM reconciliation_batches ORDER BY batch_id").fetchall(),
            "current": current,
            "freshness": db.execute("SELECT latest_authenticated_receipt_id,latest_clean_receipt_id,latest_committed_receipt_id,latest_complete_local_date FROM live_freshness").fetchone(),
            "gaps": sorted(state["evidence_gap_codes"]),
            "imports": db.execute("SELECT payload_sha256,payload_bytes FROM imports ORDER BY 1").fetchall(),
            "live": db.execute("SELECT receipt_id,result,received_at FROM import_receipts WHERE kind='live' ORDER BY receipt_id").fetchall(),
            "owner": db.execute("SELECT user_id,timezone FROM users").fetchone(),
            "versions": sorted(versions),
        }

def compare_candidate(
    database: Path,
    baseline_manifest: Path,
    baseline_source_root: Path,
    reconstruction_path: Path,
    report_path: Path,
    *,
    created_at: datetime,
) -> ComparisonResult:
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise ValueError("Comparison time must be timezone-aware")
    manifest, manifest_bytes = _read_canonical(baseline_manifest)
    plan, _ = _read_canonical(reconstruction_path)
    expected = _reference_snapshot(manifest, baseline_source_root, plan)
    actual = _actual_snapshot(database)
    binding = reconciliation_evidence_binding(database, manifest["batch_id"])
    expected_manifest = hashlib.sha256(manifest_bytes).hexdigest()
    expected_sources = hashlib.sha256(_canonical([item["sha256"] for item in manifest["sources"]])).hexdigest()
    checks = {name: actual[name] == expected[name] for name in expected}
    checks.update(manifest=binding.manifest_sha256 == expected_manifest, source_set=binding.source_set_sha256 == expected_sources)
    differences = sorted(name for name, passed in checks.items() if not passed)
    candidate_sha256 = hashlib.sha256(_canonical(actual)).hexdigest()
    outcome = "passed" if not differences else "failed"
    evidence_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"semantic:{candidate_sha256}:{outcome}"))
    with OperationalWriterLock(database.parent, blocking=True) as writer:
        with connect_operational(database, read_only=False, writer=writer) as db:
            if outcome == "failed":
                db.execute(
                    """UPDATE semantic_evidence SET outcome='failed',comparator_version=comparator_version||'-revoked'
                       WHERE user_id=? AND batch_id=? AND manifest_sha256=? AND source_set_sha256=? AND outcome='passed'""",
                    (plan["owner"], manifest["batch_id"], binding.manifest_sha256, binding.source_set_sha256),
                )
            db.execute(
                """INSERT OR IGNORE INTO semantic_evidence
                   (evidence_id,user_id,batch_id,manifest_sha256,candidate_sha256,
                    source_set_sha256,comparator_version,outcome,counts_json,created_at)
                   VALUES (?,?,?,?,?,?,'reference-1',?,?,?)""",
                (
                    evidence_id, plan["owner"], manifest["batch_id"], binding.manifest_sha256,
                    candidate_sha256, binding.source_set_sha256, outcome, binding.counts_json,
                    created_at.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                ),
            )
            db.commit()
    report = {
        "checks": checks,
        "differences": differences,
        "expected_legacy_corrections": plan["expected_legacy_corrections"],
        "outcome": outcome,
        "schema_version": 1,
    }
    _publish(report_path, _canonical(report))
    return ComparisonResult(
        not differences, len(differences), len(plan["expected_legacy_corrections"]),
        candidate_sha256, binding.source_set_sha256, checks,
    )
def build_candidate(
    installation_root: Path,
    baseline_manifest: Path,
    baseline_source_root: Path,
    reconstruction_path: Path,
    *,
    user_id: str,
    fault: FaultHook | None = None,
) -> CandidateResult:
    hook = fault or (lambda _: None)
    _private_directory(installation_root)
    datasets = installation_root / "datasets"
    legacy = datasets / "legacy"
    candidate = datasets / "candidate"
    _private_directory(datasets)
    _private_directory(legacy)
    try:
        selected = (installation_root / "current").resolve(strict=True)
    except OSError:
        raise MigrationError("Adopted storage layout is invalid") from None
    if selected != legacy:
        raise MigrationError("Legacy dataset must remain selected")
    manifest, manifest_bytes = _read_canonical(baseline_manifest)
    plan, plan_bytes = _read_canonical(reconstruction_path)
    if (
        user_id != plan.get("owner")
        or plan.get("timezone") != "Europe/Madrid"
        or manifest.get("owner") != user_id
        or len(manifest.get("sources", ())) != 6
    ):
        raise MigrationError("Migration input is invalid")

    inventory, watermark = _source_inventory(legacy)
    input_digest = hashlib.sha256(
        _canonical(
            {
                "manifest": hashlib.sha256(manifest_bytes).hexdigest(),
                "reconstruction": hashlib.sha256(plan_bytes).hexdigest(),
                "watermark": watermark,
            }
        )
    ).hexdigest()
    state_path = _state_path(candidate)
    prior: Mapping[str, Any] | None = None
    if state_path.exists():
        prior, _ = _read_canonical(state_path)
        if prior.get("input_sha256") != input_digest or prior.get("source_watermark") != watermark:
            raise MigrationError("Legacy source changed")
    resumed = prior is not None
    gate = MaintenanceGate(installation_root)
    with gate.drain():
        current_inventory, current_watermark = _source_inventory(legacy)
        if current_inventory != inventory or current_watermark != watermark:
            raise MigrationError("Legacy source changed")
        _make_directory(candidate)
        _sqlite_backup(legacy / "metadata.sqlite3", candidate / "metadata.sqlite3")
        _copy_evidence(legacy / "raw", candidate / "raw")
        _copy_evidence(legacy / "parquet", candidate / "parquet")
        database = create_operational_database(candidate, user_id=user_id)
        phase = prior.get("phase") if prior else "candidate"
        state = {
            "candidate_sha256": None,
            "evidence_gap_codes": [item["code"] for item in plan["evidence_gaps"]],
            "input_sha256": input_digest,
            "phase": phase,
            "schema_version": _STATE_VERSION,
            "source_files": len(inventory),
            "source_watermark": watermark,
        }
        if phase == "candidate":
            stage_reconciliation(database, baseline_manifest, baseline_source_root)
            phase = "baseline"
            state["phase"] = phase
            _write_state(candidate, state)
        if phase == "baseline":
            with OperationalWriterLock(candidate, blocking=True) as writer:
                with connect_operational(database, read_only=False, writer=writer) as db:
                    reconstructed = db.execute(
                        "SELECT source_watermark FROM dataset_state WHERE singleton=1"
                    ).fetchone() == (watermark,)
                    if not reconstructed:
                        db.execute("BEGIN IMMEDIATE")
                        _reconstruct(db, plan, hook)
                        db.execute(
                            "UPDATE dataset_state SET source_watermark=? WHERE singleton=1", (watermark,)
                        )
                        db.commit()
                        hook("after_reconstruction_commit")
            phase = "complete"
        candidate_sha256 = _candidate_hash(database)
        if phase == "complete":
            state.update(candidate_sha256=candidate_sha256, phase=phase)
            _write_state(candidate, state)
    final_inventory, final_watermark = _source_inventory(legacy)
    if final_inventory != inventory or final_watermark != watermark:
        raise MigrationError("Legacy source changed")
    return CandidateResult(
        resumed,
        phase,
        len(inventory),
        len(plan["evidence_gaps"]),
        watermark,
        candidate_sha256,
    )
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and verify a private storage candidate")
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--installation-root", type=Path)
    operation.add_argument("--compare-database", type=Path)
    parser.add_argument("--baseline-manifest", required=True, type=Path)
    parser.add_argument("--baseline-source-root", required=True, type=Path)
    parser.add_argument("--reconstruction", required=True, type=Path)
    parser.add_argument("--user-id")
    parser.add_argument("--report", type=Path)
    return parser
def main(arguments: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    try:
        if options.compare_database:
            if options.report is None:
                raise MigrationError("Comparison report is required")
            result = compare_candidate(
                options.compare_database, options.baseline_manifest,
                options.baseline_source_root, options.reconstruction, options.report,
                created_at=datetime.now(UTC),
            )
            print(
                "Semantic comparison complete: "
                f"outcome={'passed' if result.passed else 'failed'} "
                f"differences={result.differences}"
            )
            return 0 if result.passed else 1
        if not options.user_id:
            raise MigrationError("Candidate owner is required")
        result = build_candidate(
            options.installation_root, options.baseline_manifest,
            options.baseline_source_root, options.reconstruction, user_id=options.user_id,
        )
    except MigrationError as error:
        print(f"Storage migration failed: {error}")
        return 1
    except Exception:
        print("Storage migration failed: Internal migration failure")
        return 1
    print(
        "Candidate build complete: "
        f"phase={result.phase} source_files={result.source_files} "
        f"evidence_gaps={result.evidence_gaps} resumed={'yes' if result.resumed else 'no'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
