import json

import pytest

from app.usecase.traffic import (
    TrafficAlternative,
    TrafficIndexChange,
    TrafficIndexValue,
    TrafficJob,
    TrafficMetrics,
    TrafficScope,
)
from app.usecase.traffic_presentation import local_times, traffic_brief


def test_local_trip_minutes_are_weighted_by_served_trips() -> None:
    before = TrafficMetrics(100, 0, 1, 0, True)
    after = TrafficMetrics(80, 0, 0, 0, True)
    job = TrafficJob(
        "traffic-test",
        TrafficScope(),
        status="completed",
        baseline=before,
        alternatives=[TrafficAlternative("0", "capacity", [1], 1, 20, after, [])],
        provenance=json.dumps({"generated_vehicles_per_hour": 200, "observed_traffic": False}),
    )
    value = local_times(job)
    assert value.baseline and value.baseline.mean_trip_minutes == pytest.approx(30)
    assert value.alternatives[0].after.mean_trip_minutes == pytest.approx(24)
    payload = traffic_brief(job)
    assert "provenance" not in payload
    assert "version" not in payload
    assert "synthetic" not in json.dumps(payload)


def test_pending_brief_cannot_publish_partial_final_effects() -> None:
    job = TrafficJob(
        "traffic-test", TrafficScope(), status="running", baseline=TrafficMetrics(1, 0, 0, 0, True)
    )
    assert "baseline" not in traffic_brief(job)
    assert "alternatives" not in traffic_brief(job)


def test_brief_matches_visible_projects_and_treats_index_noise_as_unchanged() -> None:
    before = TrafficMetrics(100, 0, 0, 0, True)
    capacity = TrafficAlternative(
        "0",
        "capacity",
        [1],
        1,
        0.01,
        TrafficMetrics(99.99, 0, 0, 0, True),
        [],
        [TrafficIndexChange("Region", 99.1514048, 99.1514048, 0, 0, 1000)],
    )
    speed = TrafficAlternative(
        "1",
        "capacity",
        [1],
        1,
        1,
        TrafficMetrics(99, 0, 0, 0, True),
        [],
        [TrafficIndexChange("Region", 99.1514048, 99.1514019, -0.0000029, 0, 1000)],
    )
    job = TrafficJob(
        "traffic-test",
        TrafficScope(),
        status="completed",
        baseline=before,
        alternatives=[capacity, speed],
        provenance='{"generated_vehicles_per_hour":200}',
        indices=[TrafficIndexValue("Region", 99.1514048, 1000, 2, 100)],
    )
    payload = traffic_brief(job)
    rows = payload["alternatives"]
    assert isinstance(rows, list) and len(rows) == 1
    assert rows[0]["kind"] == "capacity"
    assert rows[0]["indices"][0]["effect"] == "unchanged"
    assert "delta" not in rows[0]["indices"][0]
    assert rows[0]["indices"][0]["after"] == 99.1514
    assert "normalization" not in json.dumps(payload)
    assert "-0.0000029" not in json.dumps(payload)
    assert job.alternatives[1].indices[0].delta == -0.0000029


def test_unconverged_local_time_does_not_become_a_recommendation() -> None:
    job = TrafficJob(
        "traffic-test",
        TrafficScope(),
        status="completed",
        baseline=TrafficMetrics(100, 0, 0, 0, True),
        provenance='{"generated_vehicles_per_hour":200}',
        alternatives=[
            TrafficAlternative("0", "capacity", [1], 1, None, TrafficMetrics(80, 0, 0, 0.1, False), [])
        ],
    )
    assert traffic_brief(job)["alternatives"] == []
