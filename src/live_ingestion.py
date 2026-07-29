from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.metric_contracts import MetricContractError, normalize_metric, parse_json_decimal
from src.operational_store import OperationalStore, ReceiptError, VersionCandidate
from src.storage import IngestResult
from src.storage_schema import connect_operational


PARSER_VERSION = "1"
CONTRACT_VERSION = "1"
_SAFE_METRIC = re.compile(r"[a-z][a-z0-9_]{0,127}")


class LiveIngestError(ValueError):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _source_metadata(headers: Mapping[str, str]) -> dict[str, str]:
    names = ("automation-name", "automation-id", "session-id")
    return {name.replace("-", "_"): headers[name] for name in names if headers.get(name)}


def _error_metric(value: Any) -> str | None:
    return value if isinstance(value, str) and _SAFE_METRIC.fullmatch(value) else None


def _row_local_timestamp(raw: str, timezone: ZoneInfo) -> datetime:
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError
    return parsed.astimezone(timezone)


def _row_local_date(row: Mapping[str, Any], timezone: ZoneInfo) -> date:
    raw = row.get("date") or row.get("startDate") or row.get("sleepStart")
    if not isinstance(raw, str):
        raise ValueError("invalid_date")
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return date.fromisoformat(raw)
        return _row_local_timestamp(raw, timezone).date()
    except ValueError:
        raise ValueError("invalid_date") from None


def _completeness(local_date: date, today: date, headers: Mapping[str, str]) -> str:
    if local_date == today:
        return "partial"
    if local_date != today - timedelta(days=1):
        raise ValueError("invalid_live_date")
    proven = all(headers.get(name) for name in ("automation-id", "session-id"))
    return "complete" if proven else "unknown"


def _metric_item(row: Sequence[str]) -> dict[str, Any]:
    local_date, value, unit, details_json = row
    item = {
        "date": local_date,
        "value": json.loads(value),
        "unit": unit,
        "samples": 1,
    }
    details = json.loads(details_json)
    if details:
        item["details"] = details
    return item


class OperationalLiveStore:
    def __init__(
        self,
        database: Path,
        *,
        user_id: str,
        timezone: str = "Europe/Madrid",
        clock: Callable[[], datetime] | None = None,
        fault: Callable[[str], None] | None = None,
    ):
        self.database = database
        self.root = database.parent
        self.user_id = user_id
        self._timezone = ZoneInfo(timezone)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._store = OperationalStore(database, user_id=user_id, fault=fault)

    def _record_rejection(
        self,
        body: bytes,
        headers: Mapping[str, str],
        received_at: datetime,
        code: str,
        *,
        contract_valid: bool = False,
        errors: Sequence[ReceiptError] = (),
    ) -> None:
        self._store.record_receipt(
            body,
            receipt_id=str(uuid.uuid4()),
            kind="live",
            parser_version=PARSER_VERSION,
            contract_version=CONTRACT_VERSION,
            source_metadata=_source_metadata(headers),
            result="rejected",
            received_at=received_at,
            contract_valid=contract_valid,
            errors=errors or (ReceiptError(code),),
        )

    def ingest(self, body: bytes, headers: Mapping[str, str]) -> IngestResult:
        received_at = self._clock()
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise RuntimeError("Live clock must be timezone-aware")
        try:
            parsed = parse_json_decimal(body)
        except MetricContractError:
            self._record_rejection(body, headers, received_at, "invalid_json")
            raise LiveIngestError(400, "Invalid JSON") from None

        container = parsed.get("data") if isinstance(parsed, Mapping) else None
        metrics = container.get("metrics") if isinstance(container, Mapping) else None
        if headers.get("automation-name") != "Default" or not isinstance(metrics, list):
            self._record_rejection(body, headers, received_at, "invalid_source_contract")
            raise LiveIngestError(422, "Invalid live export contract")

        today = received_at.astimezone(self._timezone).date()
        candidates: list[VersionCandidate] = []
        errors: list[ReceiptError] = []
        received_points = 0
        seen_identities: set[tuple[str, str]] = set()
        conflicts: set[tuple[str, str]] = set()
        for metric_group in metrics:
            name = metric_group.get("name") if isinstance(metric_group, Mapping) else None
            unit = metric_group.get("units") if isinstance(metric_group, Mapping) else None
            rows = metric_group.get("data") if isinstance(metric_group, Mapping) else None
            if not isinstance(rows, list):
                errors.append(ReceiptError("invalid_metric_group", _error_metric(name)))
                continue
            for row in rows:
                received_points += 1
                local_text: str | None = None
                try:
                    if not isinstance(row, Mapping):
                        raise ValueError("invalid_shape")
                    local_date = _row_local_date(row, self._timezone)
                    local_text = local_date.isoformat()
                    completeness = _completeness(local_date, today, headers)
                    normalized = normalize_metric(
                        name,
                        unit,
                        row,
                        completeness=completeness,
                        provenance={"automation": "Default", "local_date": local_text},
                        kind="live",
                        parser_version=PARSER_VERSION,
                        contract_version=CONTRACT_VERSION,
                    )
                    candidates.append(
                        VersionCandidate(
                            normalized.metric,
                            local_text,
                            "value",
                            normalized.source_unit,
                            normalized.canonical_unit,
                            normalized.canonical_value,
                            normalized.details_json,
                            normalized.context_fingerprint,
                            normalized.completeness,
                        )
                    )
                    identity = (normalized.metric, local_text)
                    if identity in seen_identities:
                        conflicts.add(identity)
                    seen_identities.add(identity)
                except MetricContractError as error:
                    errors.append(ReceiptError(error.code, _error_metric(name), local_text))
                except ValueError as error:
                    code = str(error) if str(error) in {"invalid_date", "invalid_live_date", "invalid_shape"} else "invalid_date"
                    errors.append(ReceiptError(code, _error_metric(name), local_text))

        if conflicts:
            candidates = [
                candidate
                for candidate in candidates
                if (candidate.metric, candidate.local_date) not in conflicts
            ]
            errors.extend(
                ReceiptError("unresolved_conflict", metric, local_date)
                for metric, local_date in sorted(conflicts)
            )
        complete_dates = {
            candidate.local_date
            for candidate in candidates
            if candidate.completeness == "complete"
        }
        result = "accepted" if candidates and not errors else "degraded" if candidates else "rejected"
        record = self._store.record_receipt(
            body,
            receipt_id=str(uuid.uuid4()),
            kind="live",
            parser_version=PARSER_VERSION,
            contract_version=CONTRACT_VERSION,
            source_metadata=_source_metadata(headers),
            result=result,
            received_at=received_at,
            contract_valid=True,
            errors=errors,
            versions=candidates,
            latest_complete_local_date=max(complete_dates, default=None),
        )
        if result == "rejected":
            raise LiveIngestError(422, "Invalid daily metrics")
        return IngestResult(
            record.import_id,
            record.duplicate_import,
            received_points,
            record.inserted_versions,
            hashlib.sha256(body).hexdigest(),
        )

    def metric_summary(self, metric: str, days: int) -> list[dict[str, Any]]:
        if not _SAFE_METRIC.fullmatch(metric) or not 1 <= days <= 3650:
            raise ValueError("Invalid metric query")
        today = self._clock().astimezone(self._timezone).date()
        since = today - timedelta(days=days - 1)
        with connect_operational(self.database) as db:
            rows = db.execute(
                """SELECT current.local_date, version.canonical_value,
                          version.canonical_unit, version.details_json
                   FROM metric_current AS current
                   JOIN metric_versions AS version
                     ON version.user_id=current.user_id
                    AND version.metric=current.metric
                    AND version.local_date=current.local_date
                    AND version.version_id=current.version_id
                   WHERE current.user_id=? AND current.metric=?
                     AND current.local_date BETWEEN ? AND ?
                     AND version.version_kind='value'
                   ORDER BY current.local_date""",
                (self.user_id, metric, since.isoformat(), today.isoformat()),
            ).fetchall()
        try:
            return [_metric_item(row) for row in rows]
        except (TypeError, json.JSONDecodeError):
            raise RuntimeError("Operational metric value is invalid") from None

    def status(self) -> dict[str, Any]:
        with connect_operational(self.database) as db:
            imports = db.execute(
                "SELECT COUNT(*) FROM imports WHERE user_id=?", (self.user_id,)
            ).fetchone()[0]
            points = db.execute(
                """SELECT COUNT(*) FROM metric_versions AS version
                   JOIN import_receipts AS receipt
                     ON receipt.user_id=version.user_id
                    AND receipt.receipt_id=version.receipt_id
                   WHERE version.user_id=? AND version.validation_status='valid'
                     AND receipt.result IN ('accepted','degraded')""",
                (self.user_id,),
            ).fetchone()[0]
            latest = db.execute(
                """SELECT received_at, source_metadata_json
                   FROM import_receipts
                   WHERE user_id=? AND kind='live' AND result IN ('accepted','degraded')
                   ORDER BY received_at DESC, receipt_id DESC LIMIT 1""",
                (self.user_id,),
            ).fetchone()
        metadata = json.loads(latest[1]) if latest else {}
        return {
            "imports": imports,
            "points": points,
            "last_import_at": latest[0] if latest else None,
            "last_automation": metadata.get("automation_name") if latest else None,
        }
