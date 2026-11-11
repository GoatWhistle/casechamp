import json
from pathlib import Path
from unittest.mock import Mock

from tests.unit.adapter.road_corridor.test_group_connectivity import network

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_jobs import NetworkJobs
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.scenario_requests import (
    CalculationQuery,
    ConnectivityEconomics,
    ConnectivityScenario,
    RecentCalculations,
)
from app.adapter.road_corridor.resolver import CorridorResolver
from app.domain.traffic_diversion import TrafficAssumptions
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors


def test_calculation_returns_durable_reference_for_the_next_turn(tmp_path: Path) -> None:
    corridors, roads = network()
    roads.data.root = tmp_path
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    result = json.loads(
        NetworkScenarios(None, corridors, None).calculate_scenario(
            ctx,
            ConnectivityScenario(
                "connectivity", ["Village A", "Village B"], selection_ids=["fast"]
            ),
        )
    )
    assert result.get("calculation_id"), "Next turn has no durable calculation reference"


def test_restarted_tools_read_and_monetize_exact_traffic_result(tmp_path: Path) -> None:

    corridors, roads = network()
    roads.data.root = tmp_path
    context = ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")
    first = Mock(deps=ChatRun(context))
    result = json.loads(
        NetworkScenarios(None, corridors, None).calculate_scenario(
            first,
            ConnectivityScenario(
                "connectivity",
                ["Village A", "Village C"],
                selection_ids=["fast"],
                traffic=TrafficAssumptions(),
            ),
        )
    )
    pair = result["pairs"][0]
    assert pair["traffic"]["displaced_flow_pcu_h"] == 1800
    assert pair["traffic"]["assigned_flow_pcu_h"] == 1800
    assert pair["traffic"]["queue_at_end_pcu"] > 0
    assert pair["after"]["hours"] > 3
    reference = result["calculation_id"]
    assert first.deps.pending[0].table.rows[0]["calculation_id"] == reference
    restarted = NetworkJobs(None, None, RoadCorridors(CorridorResolver(roads)))
    second = Mock(deps=ChatRun(context))
    assert (
        json.loads(restarted.manage_calculation(second, CalculationQuery("status", reference)))
        == result
    )
    recent = json.loads(restarted.manage_calculation(second, RecentCalculations("recent")))
    assert recent[0]["calculation_id"] == reference
    economic = json.loads(
        restarted.manage_calculation(
            second,
            ConnectivityEconomics("connectivity_economics", reference, 500),
        )
    )
    assert economic["pairs"][0]["time_cost_rub"] == pair["time_loss_pcu_hours"] * 500
    assert economic["calculation_id"] == reference
    assert economic["traffic_assumptions"]["utilization"] == 0.5
    assert len(list((tmp_path / "connectivity-results").glob("*.json"))) == 1
