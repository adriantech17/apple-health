from __future__ import annotations

import gzip
import hashlib
import json
import re
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


DATE_FORMATS = ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d")
METRIC_NAME_PATTERN = r"^[a-z0-9_]+$"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_date(point: dict[str, Any]) -> datetime | None:
    raw = point.get("date") or point.get("startDate") or point.get("sleepStart")
    if not isinstance(raw, str):
        return None
    candidate = raw.replace("Z", "+0000")
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(candidate, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            continue
    return None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


ENERGY_METRICS = {"active_energy", "basal_energy", "basal_energy_burned"}


def _canonical_measurement(metric: str, value: float, unit: str | None) -> tuple[float, str | None]:
    normalized_unit = (unit or "").strip().lower()
    if metric in ENERGY_METRICS and normalized_unit == "kj":
        return value / 4.184, "kcal"
    if metric == "blood_oxygen_saturation" and normalized_unit == "%" and value <= 1:
        return value * 100, "%"
    if metric == "walking_running_distance" and normalized_unit in {"m", "meter", "meters"}:
        return value / 1000, "km"
    return value, unit


def _point_details(metric: str, payload_json: str | None) -> dict[str, Any]:
    if not payload_json:
        return {}
    try:
        point = json.loads(payload_json)
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(point, dict):
        return {}
    if metric == "heart_rate":
        details: dict[str, Any] = {}
        minimum = _number(point.get("Min"))
        maximum = _number(point.get("Max"))
        if minimum is not None:
            details["minimum"] = minimum
        if maximum is not None:
            details["maximum"] = maximum
        return details
    if metric == "sleep_analysis":
        details = {}
        numeric_fields = {
            "awake": "awake",
            "core": "core",
            "deep": "deep",
            "rem": "rem",
            "asleep": "asleep",
            "in_bed": "inBed",
            "total_sleep": "totalSleep",
        }
        for output_name, input_name in numeric_fields.items():
            value = _number(point.get(input_name))
            if value is not None:
                details[output_name] = value
        for output_name, input_name in (
            ("sleep_start", "sleepStart"),
            ("sleep_end", "sleepEnd"),
            ("in_bed_start", "inBedStart"),
            ("in_bed_end", "inBedEnd"),
        ):
            value = point.get(input_name)
            if isinstance(value, str):
                details[output_name] = value
        return details
    return {}


def normalize(payload: Any, received_at: datetime) -> list[dict[str, Any]]:
    container = payload.get("data", payload) if isinstance(payload, dict) else {}
    metrics = container.get("metrics", []) if isinstance(container, dict) else []
    rows: list[dict[str, Any]] = []
    for metric in metrics:
        if not isinstance(metric, dict) or not isinstance(metric.get("name"), str):
            continue
        name = metric["name"]
        units = metric.get("units") if isinstance(metric.get("units"), str) else None
        data = metric.get("data", [])
        if not isinstance(data, list):
            continue
        for point in data:
            if not isinstance(point, dict):
                continue
            observed = _parse_date(point)
            if observed is None:
                continue
            event_id = hashlib.sha256(f"{name}|{units}|{_canonical(point)}".encode()).hexdigest()
            value_num = next((_number(point.get(k)) for k in ("qty", "Avg", "totalSleep", "asleep") if _number(point.get(k)) is not None), None)
            value_text = point.get("value") if isinstance(point.get("value"), str) else None
            rows.append({
                "event_id": event_id,
                "metric": name,
                "unit": units,
                "observed_at": observed,
                "value_num": value_num,
                "value_text": value_text,
                "payload_json": _canonical(point),
                "received_at": received_at,
                "year": observed.year,
                "month": observed.month,
            })
    return rows


@dataclass(frozen=True)
class IngestResult:
    import_id: str
    duplicate_request: bool
    received_points: int
    inserted_points: int
    payload_sha256: str


class HealthStore:
    def __init__(self, root: Path, timezone: str = "Europe/Madrid"):
        if not re.fullmatch(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)*", timezone):
            raise ValueError(f"Invalid timezone name: {timezone}")
        self.root = root
        self.timezone = timezone
        self.raw_dir = root / "raw"
        self.parquet_dir = root / "parquet"
        self.db_path = root / "metadata.sqlite3"
        self.lock = threading.Lock()
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS imports (
                    import_id TEXT PRIMARY KEY,
                    payload_sha256 TEXT NOT NULL UNIQUE,
                    session_id TEXT,
                    automation_id TEXT,
                    automation_name TEXT,
                    received_at TEXT NOT NULL,
                    received_points INTEGER NOT NULL,
                    inserted_points INTEGER NOT NULL,
                    raw_path TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS event_index (
                    event_id TEXT PRIMARY KEY,
                    metric TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    import_id TEXT NOT NULL REFERENCES imports(import_id)
                );
                CREATE INDEX IF NOT EXISTS event_metric_date ON event_index(metric, observed_at);
            """)

    def ingest(self, body: bytes, payload: Any, headers: dict[str, str]) -> IngestResult:
        received_at = datetime.now(UTC)
        digest = hashlib.sha256(body).hexdigest()
        rows = normalize(payload, received_at)
        with self.lock, self._connect() as db:
            existing = db.execute("SELECT import_id, received_points, inserted_points FROM imports WHERE payload_sha256=?", (digest,)).fetchone()
            if existing:
                return IngestResult(existing[0], True, existing[1], existing[2], digest)
            import_id = str(uuid.uuid4())
            raw_relative = Path(str(received_at.year)) / f"{received_at.month:02d}" / f"{received_at.strftime('%Y%m%dT%H%M%SZ')}-{digest[:12]}.json.gz"
            raw_path = self.raw_dir / raw_relative
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(raw_path, "wb", compresslevel=6) as output:
                output.write(body)
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute(
                    "INSERT INTO imports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (import_id, digest, headers.get("session-id"), headers.get("automation-id"), headers.get("automation-name"), received_at.isoformat(), len(rows), 0, str(raw_relative)),
                )
                new_rows: list[dict[str, Any]] = []
                for row in rows:
                    cursor = db.execute(
                        "INSERT OR IGNORE INTO event_index VALUES (?, ?, ?, ?)",
                        (row["event_id"], row["metric"], row["observed_at"].isoformat(), import_id),
                    )
                    if cursor.rowcount == 1:
                        new_rows.append(row)
                if new_rows:
                    table = pa.Table.from_pylist(new_rows)
                    pq.write_to_dataset(
                        table,
                        root_path=str(self.parquet_dir),
                        partition_cols=["metric", "year", "month"],
                        basename_template=f"{import_id}-{{i}}.parquet",
                        existing_data_behavior="overwrite_or_ignore",
                    )
                db.execute("UPDATE imports SET inserted_points=? WHERE import_id=?", (len(new_rows), import_id))
                db.commit()
            except Exception:
                db.rollback()
                raw_path.unlink(missing_ok=True)
                raise
        return IngestResult(import_id, False, len(rows), len(new_rows), digest)

    def status(self) -> dict[str, Any]:
        with self._connect() as db:
            imports, points = db.execute("SELECT COUNT(*), COALESCE(SUM(inserted_points), 0) FROM imports").fetchone()
            last = db.execute("SELECT received_at, automation_name FROM imports ORDER BY received_at DESC LIMIT 1").fetchone()
        return {"imports": imports, "points": points, "last_import_at": last[0] if last else None, "last_automation": last[1] if last else None}

    def metric_summary(self, metric: str, days: int) -> list[dict[str, Any]]:
        if not re.fullmatch(METRIC_NAME_PATTERN, metric):
            raise ValueError(f"Invalid metric name: {metric}")
        pattern = self.parquet_dir / f"metric={metric}" / "**" / "*.parquet"
        if not list((self.parquet_dir / f"metric={metric}").glob("**/*.parquet")):
            return []
        since = datetime.now(UTC) - timedelta(days=days)
        connection = duckdb.connect()
        try:
            result = connection.execute(
                """WITH latest AS (
                       SELECT observed_at, value_num, unit, payload_json
                       FROM read_parquet(?)
                       WHERE observed_at >= ? AND value_num IS NOT NULL
                       QUALIFY ROW_NUMBER() OVER (
                           PARTITION BY observed_at
                           ORDER BY received_at DESC
                       ) = 1
                   )
                   SELECT CAST(timezone(?, observed_at) AS DATE) AS day,
                          AVG(value_num) AS value,
                          ANY_VALUE(unit) AS unit,
                          COUNT(*) AS samples,
                          ANY_VALUE(payload_json) AS payload_json
                   FROM latest
                   GROUP BY day ORDER BY day""",
                [str(pattern), since, self.timezone],
            ).fetchall()
            summary: list[dict[str, Any]] = []
            for day, value, unit, samples, payload_json in result:
                canonical_value, canonical_unit = _canonical_measurement(metric, value, unit)
                item: dict[str, Any] = {
                    "date": str(day),
                    "value": canonical_value,
                    "unit": canonical_unit,
                    "samples": samples,
                }
                details = _point_details(metric, payload_json)
                if details:
                    item["details"] = details
                summary.append(item)
            return summary
        finally:
            connection.close()

    def prune_raw(self, retention_days: int) -> int:
        threshold = datetime.now(UTC).timestamp() - retention_days * 86400
        removed = 0
        for path in self.raw_dir.glob("**/*.json.gz"):
            if path.stat().st_mtime < threshold:
                path.unlink()
                removed += 1
        return removed
