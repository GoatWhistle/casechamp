import json

import pytest

from app.usecase.traffic import TrafficAlternative, TrafficJob, TrafficMetrics, TrafficScope
from app.usecase.traffic_presentation import local_times, traffic_brief


def test_local_trip_minutes_are_weighted_by_served_trips() -> None:
    before = TrafficMetrics(100, 0, 1, 0, True)
    after = TrafficMetrics(80, 0, 0, 0, True)
    job = TrafficJob(
        "traffic-test",
        TrafficScope(),
        status="completed",
        baseline=before,
        alternatives=[TrafficAlternative("0", "speed", [1], 1, 20, after, [])],
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
