import json

from app.adapter.chat.traffic_tools import traffic_event, traffic_reply
from app.usecase.traffic import (
    TrafficAlternative,
    TrafficIndexChange,
    TrafficJob,
    TrafficMetrics,
    TrafficRoad,
    TrafficScope,
    TrafficZone,
)


def test_chat_artifact_retains_index_and_proposal_but_fetches_geometry_separately() -> None:
    metrics = TrafficMetrics(100, 0, 2, 0, True)
    road = TrafficRoad(1, [[42, 44], [42.1, 44]], 1000, 500, 1, 0.5, True)
    effect = TrafficIndexChange("Region", 50, 51, 1, 2, 1000)
    alternative = TrafficAlternative("0", "capacity", [1], 1, 10, metrics, [road], [effect])
    job = TrafficJob(
        "traffic-test",
        TrafficScope(),
        status="completed",
        bounds=[41, 43, 43, 45],
        roads=[road],
        baseline=metrics,
        zones=[TrafficZone(42, 44, 1000)],
        alternatives=[alternative],
    )
    event = traffic_event(job)
    assert event.type == "traffic" and event.traffic
    assert event.traffic.roads == []
    assert event.traffic.zones == []
    assert event.traffic.alternatives[0].roads == []
    assert event.traffic.alternatives[0].indices == [effect]
    assert job.roads == [road]
    reply = traffic_reply(job)
    assert '"delta": 1' in reply
    assert '"coordinates"' not in reply


def test_explicit_full_result_preserves_precision_and_nonrecommended_projects() -> None:
    metrics = TrafficMetrics(100, 0, 0, 0, True)
    change = TrafficIndexChange("Region", 99.1514048, 99.1514019, -0.0000029, 0, 1000)
    job = TrafficJob(
        "traffic-test",
        TrafficScope(),
        status="completed",
        baseline=metrics,
        provenance='{"generated_vehicles_per_hour":200}',
        alternatives=[TrafficAlternative("0", "capacity", [1], 1, 0, metrics, [], [change])],
    )
    assert json.loads(traffic_reply(job))["alternatives"] == []
    full = json.loads(traffic_reply(job, full=True))
    assert full["alternatives"][0]["indices"][0]["delta"] == -0.0000029
    assert full["provenance"] == job.provenance
    assert "roads" not in full
