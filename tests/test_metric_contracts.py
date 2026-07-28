import json
from decimal import Decimal, localcontext

import pytest

from src.metric_contracts import (
    METRIC_CONTRACTS,
    MetricContractError,
    canonical_json,
    normalize_metric,
    parse_json_decimal,
)


TOTAL_CASES = (
    ("step_count", "count", "1234", "1234", "count"),
    ("active_energy", "kcal", "100.25", "100.25", "kcal"),
    ("active_energy", "kJ", "418.4", "100", "kcal"),
    ("walking_running_distance", "km", "2.75", "2.75", "km"),
    ("walking_running_distance", "m", "2750", "2.75", "km"),
    ("apple_exercise_time", "min", "45", "45", "min"),
    ("apple_stand_hour", "count", "10", "10", "count"),
    ("apple_stand_time", "min", "95", "95", "min"),
    ("flights_climbed", "count", "7", "7", "count"),
    ("time_in_daylight", "min", "80", "80", "min"),
    ("basal_energy_burned", "kcal", "1600", "1600", "kcal"),
    ("basal_energy_burned", "kJ", "6694.4", "1600", "kcal"),
)

SCALAR_CASES = (
    ("resting_heart_rate", "count/min", "62", "62", "bpm"),
    ("resting_heart_rate", "bpm", "63", "63", "bpm"),
    ("heart_rate_variability", "ms", "42.125", "42.125", "ms"),
    ("walking_heart_rate_average", "count/min", "91", "91", "bpm"),
    ("walking_heart_rate_average", "bpm", "92", "92", "bpm"),
    ("respiratory_rate", "count/min", "15.5", "15.5", "count/min"),
    ("blood_oxygen_saturation", "%", "0.975", "97.5", "%"),
    ("blood_oxygen_saturation", "%", "98", "98", "%"),
    ("walking_speed", "km/hr", "4.8", "4.8", "km/h"),
    ("walking_speed", "km/h", "4.9", "4.9", "km/h"),
    ("walking_speed", "m/s", "1.5", "5.4", "km/h"),
    ("walking_step_length", "cm", "72.5", "72.5", "cm"),
    ("walking_step_length", "m", "0.75", "75", "cm"),
    ("walking_asymmetry_percentage", "%", "0.5", "0.5", "%"),
    ("walking_double_support_percentage", "%", "27.25", "27.25", "%"),
    ("stair_speed_up", "m/s", "0.6", "0.6", "m/s"),
    ("stair_speed_up", "km/hr", "3.6", "1", "m/s"),
    ("stair_speed_up", "km/h", "7.2", "2", "m/s"),
    ("stair_speed_down", "m/s", "0.7", "0.7", "m/s"),
    ("stair_speed_down", "km/hr", "3.6", "1", "m/s"),
    ("stair_speed_down", "km/h", "7.2", "2", "m/s"),
    ("physical_effort", "kcal/hr·kg", "4.25", "4.25", "kcal/h/kg"),
    ("physical_effort", "kcal/h/kg", "4.5", "4.5", "kcal/h/kg"),
)


def normalize(name: str, unit: str, row: dict, **overrides):
    context = {
        "completeness": "complete",
        "provenance": {"source": "synthetic", "date": "2026-07-20"},
        "kind": "live",
        "parser_version": "parser-1",
        "contract_version": "daily-v1",
    }
    context.update(overrides)
    return normalize_metric(name, unit, row, **context)


def test_phase4_registry_contains_immutable_total_contracts():
    total_names = {case[0] for case in TOTAL_CASES}
    assert total_names <= set(METRIC_CONTRACTS)
    assert {METRIC_CONTRACTS[name].daily_shape for name in total_names} == {"total"}
    with pytest.raises(TypeError):
        METRIC_CONTRACTS["invented"] = METRIC_CONTRACTS["step_count"]


def test_phase4_json_numbers_are_parsed_as_decimal_and_encoded_canonically():
    parsed = parse_json_decimal('{"z":1.2300,"a":[2,0.100]}')
    assert parsed == {"z": Decimal("1.2300"), "a": [Decimal("2"), Decimal("0.100")]}
    assert canonical_json(parsed) == '{"a":[2,0.1],"z":1.23}'
    assert json.loads(canonical_json(parsed)) == {"a": [2, 0.1], "z": 1.23}


@pytest.mark.parametrize("name,unit,source,expected,canonical_unit", TOTAL_CASES)
def test_phase4_total_units_convert_without_presentation_rounding(
    name, unit, source, expected, canonical_unit
):
    result = normalize(name, unit, {"qty": Decimal(source)})
    assert result.canonical_value == expected
    assert result.source_unit == unit
    assert result.canonical_unit == canonical_unit
    assert result.details_json == "{}"
    assert result.completeness == "complete"
    assert result.provenance_json == '{"date":"2026-07-20","source":"synthetic"}'


@pytest.mark.parametrize(
    "payload,code",
    (
        ('{"qty":NaN}', "non_finite_number"),
        ('{"qty":Infinity}', "non_finite_number"),
        ('{"qty":-Infinity}', "non_finite_number"),
    ),
)
def test_phase4_parser_rejects_non_finite_json_numbers(payload, code):
    with pytest.raises(MetricContractError) as error:
        parse_json_decimal(payload)
    assert error.value.code == code


@pytest.mark.parametrize(
    "name,unit,row,code",
    (
        ("unknown_metric", "count", {"qty": Decimal("1")}, "unknown_metric"),
        ("step_count", "furlong", {"qty": Decimal("1")}, "unknown_unit"),
        ("step_count", "kcal", {"qty": Decimal("1")}, "incompatible_unit"),
        ("step_count", "count", {"qty": True}, "invalid_number"),
        ("step_count", "count", {"qty": Decimal("NaN")}, "non_finite_number"),
        ("step_count", "count", {"Avg": Decimal("1")}, "invalid_shape"),
        ("step_count", "count", {"qty": Decimal("-1")}, "invalid_value"),
    ),
)
def test_phase4_invalid_total_candidates_have_stable_sanitized_codes(name, unit, row, code):
    with pytest.raises(MetricContractError) as error:
        normalize(name, unit, row)
    assert error.value.code == code
    assert repr(row.get("qty")) not in str(error.value)


def test_phase5_registry_admits_all_scalar_contracts():
    scalar_names = {case[0] for case in SCALAR_CASES}
    assert scalar_names <= set(METRIC_CONTRACTS)
    assert {METRIC_CONTRACTS[name].daily_shape for name in scalar_names} == {"scalar"}


@pytest.mark.parametrize("name,unit,source,expected,canonical_unit", SCALAR_CASES)
def test_phase5_scalar_units_and_values_are_canonical_and_indivisible(
    name, unit, source, expected, canonical_unit
):
    result = normalize(name, unit, {"qty": Decimal(source)})
    assert (result.canonical_value, result.canonical_unit) == (expected, canonical_unit)
    assert result.source_unit == unit
    assert result.details_json == "{}"


@pytest.mark.parametrize(
    "name,unit,value,code",
    (
        ("resting_heart_rate", "count/min", True, "invalid_number"),
        ("heart_rate_variability", "ms", Decimal("Infinity"), "non_finite_number"),
        ("walking_speed", "kg", Decimal("1"), "unknown_unit"),
        ("respiratory_rate", "kcal", Decimal("1"), "incompatible_unit"),
        ("blood_oxygen_saturation", "%", Decimal("-0.01"), "invalid_value"),
        ("blood_oxygen_saturation", "%", Decimal("101"), "invalid_value"),
        ("walking_asymmetry_percentage", "%", Decimal("100.01"), "invalid_value"),
        ("walking_double_support_percentage", "%", Decimal("-0.01"), "invalid_value"),
    ),
)
def test_phase5_scalar_rejections_are_bounded_and_stable(name, unit, value, code):
    with pytest.raises(MetricContractError) as error:
        normalize(name, unit, {"qty": value})
    assert error.value.code == code


def test_phase5_scalar_shape_and_percentage_rescaling_are_metric_specific():
    with pytest.raises(MetricContractError) as error:
        normalize(
            "resting_heart_rate",
            "bpm",
            {"Min": Decimal("50"), "Avg": Decimal("65"), "Max": Decimal("90")},
        )
    assert error.value.code == "invalid_shape"
    oxygen = normalize("blood_oxygen_saturation", "%", {"qty": Decimal("0.98")})
    gait = normalize("walking_asymmetry_percentage", "%", {"qty": Decimal("0.98")})
    assert oxygen.canonical_value == "98"
    assert gait.canonical_value == "0.98"


def test_phase5_multiplicative_conversion_is_independent_of_caller_precision():
    row = {"qty": Decimal("1.234567890123456789")}
    with localcontext() as context:
        context.prec = 6
        low_precision = normalize("walking_speed", "m/s", row)
    with localcontext() as context:
        context.prec = 28
        high_precision = normalize("walking_speed", "m/s", row)
    assert low_precision.canonical_value == high_precision.canonical_value == "4.4444444044444444404"
    assert low_precision.context_fingerprint == high_precision.context_fingerprint


def sleep_row(unit_scale: Decimal = Decimal("1"), end: str = "2026-07-21T06:30:00+02:00"):
    return {
        "totalSleep": Decimal("7.5") * unit_scale,
        "asleep": Decimal("7.5") * unit_scale,
        "awake": Decimal("0.5") * unit_scale,
        "core": Decimal("4.5") * unit_scale,
        "deep": Decimal("1") * unit_scale,
        "rem": Decimal("2") * unit_scale,
        "inBed": Decimal("8") * unit_scale,
        "sleepStart": "2026-07-20T22:30:00+02:00",
        "sleepEnd": end,
        "inBedStart": "2026-07-20T22:30:00+02:00",
        "inBedEnd": end,
    }


def test_phase6_registry_is_the_complete_25_metric_authority():
    expected = {case[0] for case in (*TOTAL_CASES, *SCALAR_CASES)} | {
        "heart_rate",
        "sleep_analysis",
        "vo2_max",
        "cardio_recovery",
    }
    assert len(expected) == 25
    assert set(METRIC_CONTRACTS) == expected
    assert METRIC_CONTRACTS["heart_rate"].daily_shape == "composite"
    assert METRIC_CONTRACTS["sleep_analysis"].daily_shape == "sleep"
    assert METRIC_CONTRACTS["vo2_max"].daily_shape == "sparse"
    assert METRIC_CONTRACTS["cardio_recovery"].daily_shape == "sparse"
    assert all(
        contract.identity_forms == frozenset({"date_only", "offset_timestamp"})
        for contract in METRIC_CONTRACTS.values()
    )


@pytest.mark.parametrize("unit", ("count/min", "bpm"))
def test_phase6_heart_rate_preserves_aligned_average_extrema_and_unit(unit):
    result = normalize(
        "heart_rate",
        unit,
        {"Min": Decimal("48"), "Avg": Decimal("64.5"), "Max": Decimal("121")},
    )
    assert (result.canonical_value, result.canonical_unit) == ("64.5", "bpm")
    assert result.details_json == '{"maximum":121,"minimum":48}'
    assert result.source_unit == unit


@pytest.mark.parametrize(
    "row,code",
    (
        ({"Min": Decimal("70"), "Avg": Decimal("65"), "Max": Decimal("90")}, "invalid_details"),
        ({"Min": Decimal("50"), "Avg": Decimal("95"), "Max": Decimal("90")}, "invalid_details"),
        ({"Min": Decimal("50"), "Avg": True, "Max": Decimal("90")}, "invalid_number"),
        ({"Min": Decimal("50"), "Avg": Decimal("65")}, "invalid_shape"),
    ),
)
def test_phase6_heart_rate_rejects_unaligned_or_invalid_extrema(row, code):
    with pytest.raises(MetricContractError) as error:
        normalize("heart_rate", "bpm", row)
    assert error.value.code == code


@pytest.mark.parametrize(
    "unit,row,expected",
    (
        ("hr", sleep_row(), "7.5"),
        ("h", sleep_row(), "7.5"),
        ("min", sleep_row(Decimal("60")), "7.5"),
        ("hr", sleep_row(end="2026-07-21T06:31:00+02:00"), "7.5"),
    ),
)
def test_phase6_sleep_preserves_one_row_with_validated_stages_and_intervals(unit, row, expected):
    result = normalize("sleep_analysis", unit, row)
    details = json.loads(result.details_json, parse_float=Decimal, parse_int=Decimal)
    assert (result.canonical_value, result.canonical_unit) == (expected, "h")
    assert details["core"] == Decimal("4.5")
    assert details["deep"] == Decimal("1")
    assert details["rem"] == Decimal("2")
    assert details["sleep_start"] == "2026-07-20T22:30:00+02:00"
    assert details["sleep_end"] == row["sleepEnd"]


def test_phase6_sleep_does_not_fill_optional_asleep_or_in_bed_details():
    row = sleep_row()
    for field in ("asleep", "inBed", "inBedStart", "inBedEnd"):
        row.pop(field)
    result = normalize("sleep_analysis", "hr", row)
    details = json.loads(result.details_json, parse_float=Decimal, parse_int=Decimal)
    assert result.canonical_value == "7.5"
    assert "asleep" not in details
    assert "in_bed" not in details


@pytest.mark.parametrize(
    "mutation,code",
    (
        ({"core": Decimal("4")}, "invalid_details"),
        ({"sleepEnd": "2026-07-21T06:32:00+02:00"}, "invalid_details"),
        ({"sleepEnd": "2026-07-21T06:30:00"}, "invalid_details"),
        ({"deep": True}, "invalid_number"),
        ({"rem": Decimal("NaN")}, "non_finite_number"),
    ),
)
def test_phase6_sleep_rejects_inconsistent_or_malformed_details(mutation, code):
    row = sleep_row()
    row.update(mutation)
    with pytest.raises(MetricContractError) as error:
        normalize("sleep_analysis", "hr", row)
    assert error.value.code == code


def test_phase6_sleep_rejects_disjoint_duration_consistent_in_bed_interval():
    row = sleep_row()
    row.update(
        inBedStart="2026-07-20T10:00:00+02:00",
        inBedEnd="2026-07-20T18:00:00+02:00",
    )
    with pytest.raises(MetricContractError) as error:
        normalize("sleep_analysis", "hr", row)
    assert error.value.code == "invalid_details"


@pytest.mark.parametrize(
    "name,unit,value,expected,canonical_unit",
    (
        ("vo2_max", "mL/min·kg", "42.75", "42.75", "mL/kg/min"),
        ("vo2_max", "mL/kg/min", "43", "43", "mL/kg/min"),
        ("cardio_recovery", "count/min", "28", "28", "bpm"),
        ("cardio_recovery", "bpm", "29", "29", "bpm"),
    ),
)
def test_phase6_sparse_metrics_preserve_only_observed_values(name, unit, value, expected, canonical_unit):
    result = normalize(name, unit, {"qty": Decimal(value)})
    assert (result.canonical_value, result.canonical_unit) == (expected, canonical_unit)
    with pytest.raises(MetricContractError) as error:
        normalize(name, unit, {"qty": None})
    assert error.value.code == "invalid_number"


def test_phase6_context_fingerprint_is_stable_and_excludes_receipt_mechanics():
    row = {"Min": Decimal("48"), "Avg": Decimal("64.5"), "Max": Decimal("121")}
    first = normalize(
        "heart_rate",
        "bpm",
        row,
        provenance={"receipt_id": "first", "received_at": "2026-07-20T12:00:00Z", "authority": 1},
    )
    retry = normalize(
        "heart_rate",
        "bpm",
        row,
        provenance={"receipt_id": "retry", "received_at": "2026-07-20T12:05:00Z", "authority": 2},
    )
    changed = normalize("heart_rate", "bpm", row, completeness="partial")
    batched = normalize(
        "heart_rate",
        "bpm",
        row,
        trusted_batch_context={"manifest": "synthetic", "scope": "baseline"},
    )
    assert first.context_fingerprint == retry.context_fingerprint
    assert first.context_fingerprint != changed.context_fingerprint
    assert first.context_fingerprint != batched.context_fingerprint
    assert len(first.context_fingerprint) == 64


def test_phase6_every_contract_has_a_valid_shape_accepted_unit_and_incompatible_example():
    sample_rows = {
        "total": {"qty": Decimal("1")},
        "scalar": {"qty": Decimal("1")},
        "sparse": {"qty": Decimal("1")},
        "composite": {"Min": Decimal("1"), "Avg": Decimal("2"), "Max": Decimal("3")},
        "sleep": sleep_row(),
    }
    validated = []
    for name, contract in METRIC_CONTRACTS.items():
        accepted_unit = sorted(contract.accepted_source_units)[0]
        result = normalize(name, accepted_unit, sample_rows[contract.daily_shape])
        validated.append(result.metric)
        incompatible = next(
            unit
            for candidate in METRIC_CONTRACTS.values()
            for unit in candidate.accepted_source_units
            if unit not in contract.accepted_source_units
        )
        with pytest.raises(MetricContractError) as error:
            normalize(name, incompatible, sample_rows[contract.daily_shape])
        assert error.value.code == "incompatible_unit"
    assert set(validated) == set(METRIC_CONTRACTS)
