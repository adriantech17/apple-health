import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.storage import HealthStore, normalize


def sample() -> dict:
    return {
        "data": {
            "metrics": [
                {
                    "name": "step_count",
                    "units": "count",
                    "data": [{"qty": 1000, "date": recent_date()}],
                }
            ]
        }
    }


def recent_date() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d 12:00:00 +0000")


def test_normalize_builds_stable_event_id():
    now = datetime(2026, 7, 11, tzinfo=UTC)
    payload = sample()
    first = normalize(payload, now)
    second = normalize(payload, now)
    assert len(first) == 1
    assert first[0]["event_id"] == second[0]["event_id"]
    assert first[0]["observed_at"].isoformat() == datetime.strptime(
        payload["data"]["metrics"][0]["data"][0]["date"],
        "%Y-%m-%d %H:%M:%S %z",
    ).isoformat()


def test_ingest_is_idempotent(tmp_path: Path):
    store = HealthStore(tmp_path)
    body = json.dumps(sample(), sort_keys=True).encode()
    first = store.ingest(body, sample(), {"session-id": "abc"})
    second = store.ingest(body, sample(), {"session-id": "abc"})
    assert first.inserted_points == 1
    assert second.duplicate_request is True
    assert store.status()["points"] == 1


def test_metric_summary_converts_energy_to_kcal(tmp_path: Path):
    store = HealthStore(tmp_path)
    payload = {
        "data": {
            "metrics": [
                {
                    "name": "active_energy",
                    "units": "kJ",
                    "data": [{"qty": 418.4, "date": recent_date()}],
                }
            ]
        }
    }
    store.ingest(json.dumps(payload).encode(), payload, {})
    result = store.metric_summary("active_energy", 30)
    assert result[0]["value"] == pytest.approx(100)
    assert result[0]["unit"] == "kcal"


def test_metric_summary_exposes_heart_rate_range(tmp_path: Path):
    store = HealthStore(tmp_path)
    payload = {
        "data": {
            "metrics": [
                {
                    "name": "heart_rate",
                    "units": "count/min",
                    "data": [
                        {
                            "Min": 48,
                            "Avg": 64.5,
                            "Max": 121,
                            "date": recent_date(),
                        }
                    ],
                }
            ]
        }
    }
    store.ingest(json.dumps(payload).encode(), payload, {})
    result = store.metric_summary("heart_rate", 30)
    assert result[0]["value"] == 64.5
    assert result[0]["details"] == {"minimum": 48.0, "maximum": 121.0}


def test_metric_summary_exposes_sleep_stages(tmp_path: Path):
    store = HealthStore(tmp_path)
    payload = {
        "data": {
            "metrics": [
                {
                    "name": "sleep_analysis",
                    "units": "hr",
                    "data": [
                        {
                            "totalSleep": 8.0,
                            "awake": 0.5,
                            "core": 4.5,
                            "deep": 1.0,
                            "rem": 2.0,
                            "sleepStart": "2026-07-09 23:00:00 +0200",
                            "sleepEnd": "2026-07-10 07:30:00 +0200",
                            "date": recent_date(),
                        }
                    ],
                }
            ]
        }
    }
    store.ingest(json.dumps(payload).encode(), payload, {})
    result = store.metric_summary("sleep_analysis", 30)
    assert result[0]["value"] == 8.0
    assert result[0]["details"]["deep"] == 1.0
    assert result[0]["details"]["rem"] == 2.0
    assert result[0]["details"]["sleep_start"] == "2026-07-09 23:00:00 +0200"


@pytest.mark.parametrize("metric", ["../step_count", "step/count", "Métrica"])
def test_metric_summary_rejects_invalid_identifiers(tmp_path: Path, metric: str):
    store = HealthStore(tmp_path)

    with pytest.raises(ValueError, match="Invalid metric name"):
        store.metric_summary(metric, 30)
