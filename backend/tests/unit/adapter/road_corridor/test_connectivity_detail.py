import json
from pathlib import Path
from unittest.mock import Mock

from tests.unit.adapter.road_corridor.test_group_connectivity import network

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_jobs import NetworkJobs
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.scenario_requests import CalculationQuery, ConnectivityScenario
from app.domain.traffic_diversion import TrafficAssumptions
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext


def test_summary_preserves_numbers_and_full_result_remains_available(tmp_path: Path) -> None:
    corridors, roads = network()
    roads.data.root = tmp_path
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    response = NetworkScenarios(None, corridors, None).calculate_scenario(
        ctx,
        ConnectivityScenario(
            "connectivity",
            ["Village A", "Village C"],
            selection_ids=["fast"],
            traffic=TrafficAssumptions(),
        ),
    )
    summary = json.loads(response)
    reference = summary["calculation_id"]
    tools = NetworkJobs(None, None, corridors)
    full = tools.manage_calculation(ctx, CalculationQuery("status", reference, detail="full"))
    saved = json.loads(full)
    assert full == corridors.read_connectivity(reference)
    assert "closed_way_ids" not in summary
    assert summary["closed_way_count"] == len(saved["closed_way_ids"]) == 1
    assert summary["traffic_assumptions"] == saved["traffic_assumptions"]
    pair, original = summary["pairs"][0], saved["pairs"][0]
    for key in ("before", "after", "score_before", "score_after", "delta", "time_loss_pcu_hours"):
        assert pair[key] == original[key]
    assert "assumptions" not in pair["traffic"]
    assert pair["traffic"]["assigned_flow_pcu_h"] == original["traffic"]["assigned_flow_pcu_h"]
    for route, source in zip(pair["traffic"]["routes"], original["traffic"]["routes"], strict=True):
        assert route["mean_hours"] == source["mean_hours"]
        assert "way_ids" not in route["route"]
        assert route["route"]["way_count"] == len(source["route"]["way_ids"])
        assert route["route"]["assumed_lane_way_count"] == len(source["route"]["assumed_lane_ways"])
    assert tools.manage_calculation(ctx, CalculationQuery("status", reference)) == response
