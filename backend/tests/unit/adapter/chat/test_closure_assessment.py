import json
from unittest.mock import Mock

from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.scenario_requests import SelectionClosure
from app.usecase.road_corridor import CorridorRegion, RoadCorridor
from app.usecase.road_graph import RoadChange, RoadJob
from app.usecase.road_stress import StressJob, StressSummary


def test_default_closure_returns_indices_and_impact_for_the_same_roads() -> None:
    stress = Mock()
    stress.get.return_value = stress.submit.return_value = StressJob("stress", "v", [10, 11])
    stress.summary.return_value = StressSummary(
        "stress", "v", "queued", "preparing", 2, None, "", None, 0, 0, 0, 0, 180
    )
    stress.geometry.return_value.names = ["М-10", "М-11"]
    roads, corridors, ctx = Mock(), Mock(), Mock()
    corridor = RoadCorridor(
        "selection",
        "М-10; М-11",
        "Москва",
        "Санкт-Петербург",
        [10, 11],
        10,
        0,
        0,
        [CorridorRegion("50", "Московская область")],
        [],
    )
    corridors.get.return_value = corridor
    corridors.recent_connectivity.return_value = "[]"
    roads.closure_jobs.return_value = []
    roads.submit_closure.return_value = [
        RoadJob(
            "index",
            "50",
            "Московская область",
            "road",
            [RoadChange(10, 0), RoadChange(11, 0)],
            "queued",
            0,
            360,
            "v",
        )
    ]
    ctx.deps.pending = []
    ctx.deps.context.region_id = "26"
    result = json.loads(
        NetworkScenarios(roads, corridors, None, stress).calculate_scenario(
            ctx, SelectionClosure("close_selection", ["selection"])
        )
    )
    roads.submit_closure.assert_called_once_with([10, 11], ["50"], "v")
    assert result["indices"][0]["id"] == "index"
    assert result["indices"][0]["status"] == "queued"
    assert {event.type for event in ctx.deps.pending} == {"calculation", "stress_test"}
