from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
from types import MappingProxyType
from typing import Any, Callable


JsonValue = None | bool | str | int | Decimal | Mapping[str, "JsonValue"] | Sequence["JsonValue"]
DecimalConverter = Callable[[Decimal], Decimal]
DecimalValidator = Callable[[Decimal], bool]


class MetricContractError(ValueError):
    """A privacy-safe metric validation failure with a stable machine code."""

    def __init__(self, code: str, metric: str | None = None):
        self.code = code
        self.metric = metric
        suffix = f" for metric {metric}" if metric else ""
        super().__init__(f"{code}{suffix}")


@dataclass(frozen=True)
class UnitConversion:
    source_unit: str
    convert: DecimalConverter


@dataclass(frozen=True)
class MetricContract:
    name: str
    daily_shape: str
    identity_forms: frozenset[str]
    conversions: tuple[UnitConversion, ...]
    canonical_unit: str
    validate: DecimalValidator
    limitation: str

    @property
    def accepted_source_units(self) -> frozenset[str]:
        return frozenset(item.source_unit for item in self.conversions)


@dataclass(frozen=True)
class NormalizedMetric:
    metric: str
    canonical_value: str
    source_unit: str
    canonical_unit: str
    details_json: str
    completeness: str
    provenance_json: str
    context_fingerprint: str


def _error(code: str, metric: str | None = None) -> MetricContractError:
    return MetricContractError(code, metric)


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise _error("non_finite_number")
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def canonical_json(value: JsonValue) -> str:
    """Encode JSON deterministically while retaining Decimal values as numbers."""

    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise _error("invalid_json")
        return "{" + ",".join(
            f"{canonical_json(key)}:{canonical_json(value[key])}" for key in sorted(value)
        ) + "}"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    raise _error("invalid_json")


def parse_json_decimal(payload: str | bytes | bytearray) -> Any:
    """Parse every JSON number directly as Decimal and reject non-finite tokens."""

    def reject_constant(_: str) -> None:
        raise _error("non_finite_number")

    try:
        return json.loads(
            payload,
            parse_float=Decimal,
            parse_int=Decimal,
            parse_constant=reject_constant,
        )
    except MetricContractError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise _error("invalid_json") from exc


def _identity(value: Decimal) -> Decimal:
    return value


def _multiply(factor: str) -> DecimalConverter:
    def convert(value: Decimal) -> Decimal:
        with localcontext() as context:
            context.prec = 50
            return value * Decimal(factor)

    return convert


def _divide(divisor: str) -> DecimalConverter:
    def convert(value: Decimal) -> Decimal:
        with localcontext() as context:
            context.prec = 50
            return value / Decimal(divisor)

    return convert


def _nonnegative(value: Decimal) -> bool:
    return value >= 0


def _percentage(value: Decimal) -> bool:
    return Decimal("0") <= value <= Decimal("100")


def _oxygen_percent(value: Decimal) -> Decimal:
    return value * Decimal("100") if Decimal("0") <= value <= Decimal("1") else value


def _measurement(
    name: str,
    daily_shape: str,
    canonical_unit: str,
    conversions: tuple[tuple[str, DecimalConverter], ...],
    validate: DecimalValidator,
    limitation: str,
) -> MetricContract:
    return MetricContract(
        name=name,
        daily_shape=daily_shape,
        identity_forms=frozenset({"date_only", "offset_timestamp"}),
        conversions=tuple(UnitConversion(unit, converter) for unit, converter in conversions),
        canonical_unit=canonical_unit,
        validate=validate,
        limitation=limitation,
    )


def _total(
    name: str,
    canonical_unit: str,
    conversions: tuple[tuple[str, DecimalConverter], ...],
) -> MetricContract:
    return _measurement(
        name,
        "total",
        canonical_unit,
        conversions,
        _nonnegative,
        "One selected daily total; versions are never aggregated together.",
    )


def _scalar(
    name: str,
    canonical_unit: str,
    conversions: tuple[tuple[str, DecimalConverter], ...],
    validate: DecimalValidator = _nonnegative,
) -> MetricContract:
    return _measurement(
        name,
        "scalar",
        canonical_unit,
        conversions,
        validate,
        "One selected daily scalar; missing dates remain absent.",
    )


_TOTAL_CONTRACTS = (
    _total("step_count", "count", (("count", _identity),)),
    _total("active_energy", "kcal", (("kcal", _identity), ("kJ", _divide("4.184")))),
    _total("walking_running_distance", "km", (("km", _identity), ("m", _divide("1000")))),
    _total("apple_exercise_time", "min", (("min", _identity),)),
    _total("apple_stand_hour", "count", (("count", _identity),)),
    _total("apple_stand_time", "min", (("min", _identity),)),
    _total("flights_climbed", "count", (("count", _identity),)),
    _total("time_in_daylight", "min", (("min", _identity),)),
    _total("basal_energy_burned", "kcal", (("kcal", _identity), ("kJ", _divide("4.184")))),
)

_SCALAR_CONTRACTS = (
    _scalar("resting_heart_rate", "bpm", (("count/min", _identity), ("bpm", _identity))),
    _scalar("heart_rate_variability", "ms", (("ms", _identity),)),
    _scalar("walking_heart_rate_average", "bpm", (("count/min", _identity), ("bpm", _identity))),
    _scalar("respiratory_rate", "count/min", (("count/min", _identity),)),
    _scalar("blood_oxygen_saturation", "%", (("%", _oxygen_percent),), _percentage),
    _scalar("walking_speed", "km/h", (("km/hr", _identity), ("km/h", _identity), ("m/s", _multiply("3.6")))),
    _scalar("walking_step_length", "cm", (("cm", _identity), ("m", _multiply("100")))),
    _scalar("walking_asymmetry_percentage", "%", (("%", _identity),), _percentage),
    _scalar("walking_double_support_percentage", "%", (("%", _identity),), _percentage),
    _scalar("stair_speed_up", "m/s", (("m/s", _identity), ("km/hr", _divide("3.6")), ("km/h", _divide("3.6")))),
    _scalar("stair_speed_down", "m/s", (("m/s", _identity), ("km/hr", _divide("3.6")), ("km/h", _divide("3.6")))),
    _scalar("physical_effort", "kcal/h/kg", (("kcal/hr·kg", _identity), ("kcal/h/kg", _identity))),
)

_SPECIAL_CONTRACTS = (
    _measurement(
        "heart_rate",
        "composite",
        "bpm",
        (("count/min", _identity), ("bpm", _identity)),
        _nonnegative,
        "Minimum, average, and maximum remain aligned to one selected daily row.",
    ),
    _measurement(
        "sleep_analysis",
        "sleep",
        "h",
        (("hr", _identity), ("h", _identity), ("min", _divide("60"))),
        _nonnegative,
        "Sleep stages and intervals remain aligned; missing stages are not inferred.",
    ),
    _measurement(
        "vo2_max",
        "sparse",
        "mL/kg/min",
        (("mL/min·kg", _identity), ("mL/kg/min", _identity)),
        _nonnegative,
        "Sparse observations remain absent on unobserved dates.",
    ),
    _measurement(
        "cardio_recovery",
        "sparse",
        "bpm",
        (("count/min", _identity), ("bpm", _identity)),
        _nonnegative,
        "Sparse observations remain absent on unobserved dates.",
    ),
)


METRIC_CONTRACTS: Mapping[str, MetricContract] = MappingProxyType(
    {
        contract.name: contract
        for contract in (*_TOTAL_CONTRACTS, *_SCALAR_CONTRACTS, *_SPECIAL_CONTRACTS)
    }
)
_KNOWN_SOURCE_UNITS = frozenset(
    conversion.source_unit
    for contract in METRIC_CONTRACTS.values()
    for conversion in contract.conversions
)


def _as_decimal(value: Any, metric: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int)):
        raise _error("invalid_number", metric)
    parsed = value if isinstance(value, Decimal) else Decimal(value)
    if not parsed.is_finite():
        raise _error("non_finite_number", metric)
    return parsed


def _conversion(contract: MetricContract, source_unit: str) -> DecimalConverter:
    for conversion in contract.conversions:
        if conversion.source_unit == source_unit:
            return conversion.convert
    code = "incompatible_unit" if source_unit in _KNOWN_SOURCE_UNITS else "unknown_unit"
    raise _error(code, contract.name)


def _interval_time(value: Any, metric: str) -> datetime:
    if not isinstance(value, str):
        raise _error("invalid_details", metric)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _error("invalid_details", metric) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _error("invalid_details", metric)
    return parsed


def _duration_hours(start: datetime, end: datetime, metric: str) -> Decimal:
    difference = end - start
    if difference <= timedelta(0):
        raise _error("invalid_details", metric)
    microseconds = (
        (difference.days * 86_400 + difference.seconds) * 1_000_000
        + difference.microseconds
    )
    with localcontext() as context:
        context.prec = 50
        return Decimal(microseconds) / Decimal("3600000000")


def _within_one_minute(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) * Decimal("60") <= Decimal("1")


def _present_fields(row: Mapping[str, Any], fields: Sequence[str]) -> tuple[str, ...]:
    return tuple(field for field in fields if field in row)


def _simple_row(
    row: Mapping[str, Any],
    contract: MetricContract,
    converter: DecimalConverter,
) -> tuple[Decimal, Mapping[str, JsonValue]]:
    if "qty" not in row:
        raise _error("invalid_shape", contract.name)
    value = converter(_as_decimal(row["qty"], contract.name))
    if not contract.validate(value):
        raise _error("invalid_value", contract.name)
    return value, {}


def _heart_rate_row(
    row: Mapping[str, Any],
    contract: MetricContract,
    converter: DecimalConverter,
) -> tuple[Decimal, Mapping[str, JsonValue]]:
    required = ("Min", "Avg", "Max")
    if not all(field in row for field in required):
        raise _error("invalid_shape", contract.name)
    minimum, average, maximum = (
        converter(_as_decimal(row[field], contract.name)) for field in required
    )
    if not all(contract.validate(value) for value in (minimum, average, maximum)):
        raise _error("invalid_value", contract.name)
    if not minimum <= average <= maximum:
        raise _error("invalid_details", contract.name)
    return average, {"minimum": minimum, "maximum": maximum}


def _sleep_row(
    row: Mapping[str, Any],
    contract: MetricContract,
    converter: DecimalConverter,
) -> tuple[Decimal, Mapping[str, JsonValue]]:
    required_durations = ("totalSleep", "awake", "core", "deep", "rem")
    required_intervals = ("sleepStart", "sleepEnd")
    if not all(field in row for field in (*required_durations, *required_intervals)):
        raise _error("invalid_shape", contract.name)
    optional_in_bed = ("inBed", "inBedStart", "inBedEnd")
    if any(field in row for field in optional_in_bed) and not all(
        field in row for field in optional_in_bed
    ):
        raise _error("invalid_shape", contract.name)
    duration_fields = (*required_durations, *_present_fields(row, ("asleep", "inBed")))
    durations = {
        field: converter(_as_decimal(row[field], contract.name)) for field in duration_fields
    }
    if not all(contract.validate(value) for value in durations.values()):
        raise _error("invalid_value", contract.name)
    total = durations["totalSleep"]
    if "asleep" in durations and not _within_one_minute(total, durations["asleep"]):
        raise _error("invalid_details", contract.name)
    if not _within_one_minute(total, sum(durations[field] for field in ("core", "deep", "rem"))):
        raise _error("invalid_details", contract.name)

    parsed_intervals = {
        field: _interval_time(row[field], contract.name)
        for field in (*required_intervals, *_present_fields(row, optional_in_bed[1:]))
    }
    sleep_interval = _duration_hours(
        parsed_intervals["sleepStart"], parsed_intervals["sleepEnd"], contract.name
    )
    expected_interval = total + durations["awake"]
    if not _within_one_minute(sleep_interval, expected_interval):
        raise _error("invalid_details", contract.name)
    if "inBed" in durations:
        in_bed_interval = _duration_hours(
            parsed_intervals["inBedStart"], parsed_intervals["inBedEnd"], contract.name
        )
        if not _within_one_minute(in_bed_interval, durations["inBed"]):
            raise _error("invalid_details", contract.name)
        if (
            parsed_intervals["inBedStart"] > parsed_intervals["sleepStart"]
            or parsed_intervals["inBedEnd"] < parsed_intervals["sleepEnd"]
        ):
            raise _error("invalid_details", contract.name)
        if durations["inBed"] < total:
            raise _error("invalid_details", contract.name)

    details: dict[str, JsonValue] = {
        "awake": durations["awake"],
        "core": durations["core"],
        "deep": durations["deep"],
        "rem": durations["rem"],
        "sleep_start": row["sleepStart"],
        "sleep_end": row["sleepEnd"],
    }
    if "asleep" in durations:
        details["asleep"] = durations["asleep"]
    if "inBed" in durations:
        details.update(
            {
                "in_bed": durations["inBed"],
                "in_bed_start": row["inBedStart"],
                "in_bed_end": row["inBedEnd"],
            }
        )
    return total, details


def _normalize_row(
    row: Mapping[str, Any],
    contract: MetricContract,
    converter: DecimalConverter,
) -> tuple[Decimal, Mapping[str, JsonValue]]:
    if contract.daily_shape == "composite":
        return _heart_rate_row(row, contract, converter)
    if contract.daily_shape == "sleep":
        return _sleep_row(row, contract, converter)
    return _simple_row(row, contract, converter)


def _fingerprint(
    contract: MetricContract,
    source_unit: str,
    value: str,
    details_json: str,
    completeness: str,
    kind: str,
    parser_version: str,
    contract_version: str,
    trusted_batch_context: Mapping[str, JsonValue] | None,
) -> str:
    content = {
        "canonical_unit": contract.canonical_unit,
        "canonical_value": value,
        "completeness": completeness,
        "contract_version": contract_version,
        "details": parse_json_decimal(details_json),
        "kind": kind,
        "metric_contract": {
            "accepted_source_units": sorted(contract.accepted_source_units),
            "canonical_unit": contract.canonical_unit,
            "daily_shape": contract.daily_shape,
            "identity_forms": sorted(contract.identity_forms),
            "name": contract.name,
        },
        "parser_version": parser_version,
        "source_unit": source_unit,
        "trusted_batch_context": trusted_batch_context,
    }
    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def normalize_metric(
    name: str,
    source_unit: str,
    row: Mapping[str, Any],
    *,
    completeness: str,
    provenance: Mapping[str, JsonValue],
    kind: str,
    parser_version: str,
    contract_version: str,
    trusted_batch_context: Mapping[str, JsonValue] | None = None,
) -> NormalizedMetric:
    contract = METRIC_CONTRACTS.get(name)
    if contract is None:
        raise _error("unknown_metric", name)
    if not isinstance(source_unit, str):
        raise _error("unknown_unit", name)
    if not isinstance(row, Mapping):
        raise _error("invalid_shape", name)
    if completeness not in {"partial", "complete", "unknown"}:
        raise _error("invalid_completeness", name)
    if not all(isinstance(item, str) and item for item in (kind, parser_version, contract_version)):
        raise _error("invalid_context", name)

    converter = _conversion(contract, source_unit)
    converted, details = _normalize_row(row, contract, converter)
    canonical_value = _decimal_text(converted)
    details_json = canonical_json(details)
    try:
        provenance_json = canonical_json(provenance)
        fingerprint = _fingerprint(
            contract,
            source_unit,
            canonical_value,
            details_json,
            completeness,
            kind,
            parser_version,
            contract_version,
            trusted_batch_context,
        )
    except MetricContractError as exc:
        raise _error("invalid_context", name) from exc
    return NormalizedMetric(
        metric=name,
        canonical_value=canonical_value,
        source_unit=source_unit,
        canonical_unit=contract.canonical_unit,
        details_json=details_json,
        completeness=completeness,
        provenance_json=provenance_json,
        context_fingerprint=fingerprint,
    )
