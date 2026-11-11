import json
from unittest.mock import Mock

import pytest
from pydantic import TypeAdapter, ValidationError

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_jobs import NetworkJobs
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.network_search import NetworkSearch
from app.adapter.chat.scenario_requests import (
    CalculationQuery,
    NetworkScenario,
    RoadEdit,
    ServiceEdit,
    TransportScenario,
)
from app.adapter.chat.transport_requests import RoadSearch
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridor, RoadRoute
from app.usecase.road_graph import RoadChange, RoadJob
from app.usecase.transport_links import LinkChange


def context() -> Mock:
    return Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))


@pytest.mark.parametrize("name", [None, "R-1"])
def test_one_search_interface_selects_endpoint_or_named_road_search(name: str | None) -> None:
    corridors = Mock()
    corridor = RoadCorridor("id", "R-1", "A", "B", [7], 1, 0, 0, [], [])
    corridors.resolve_route.return_value = RoadRoute(corridor, 1)
    corridors.resolve.return_value = corridor
    result = json.loads(
        NetworkSearch(None, corridors).find_transport(
            context(),
            RoadSearch("road", "Town A", "Town B", name),
        )
    )
    assert result["id"] == "id"
    if name:
        corridors.resolve.assert_called_once_with(name, "Town A", "Town B")
        corridors.resolve_route.assert_not_called()
    else:
        corridors.resolve_route.assert_called_once_with("Town A", "Town B")
        corridors.resolve.assert_not_called()


def test_roads_and_aviation_submit_together_and_keep_the_calculation_card() -> None:
    graph = Mock()
    road = RoadChange(7, 1.2)
    link = LinkChange("remove", "intercity", "air", "City", "*")
    graph.geometry.return_value = Mock(
        names=["Road"],
        length_km=1,
        lines=[[[40.0, 44.0], [41.0, 45.0]]],
    )
    graph.submit.return_value = RoadJob(
        "joint",
        "region",
        "Region",
        "road",
        [road],
        "queued",
        0,
        360,
        "v",
        links=[link],
    )
    ctx = context()
    result = json.loads(
        NetworkScenarios(graph, None, None).calculate_scenario(
            ctx,
            NetworkScenario(
                "network",
                ["region"],
                "road",
                [RoadEdit(7, 1.2)],
                [ServiceEdit("remove", "intercity", "air", "City", "*")],
            ),
        )
    )
    graph.submit.assert_called_once_with(
        "region",
        "road",
        [road],
        [link],
        queue=True,
        appraisal=None,
    )
    assert result[0]["id"] == "joint"
    assert ctx.deps.pending[0].calculation.job_ids == ["joint"]


def test_reading_a_saved_result_uses_the_job_interface_without_resubmission() -> None:
    graph = Mock()
    graph.job.return_value = RoadJob("saved", "1", "Region", "road", [], "completed", 360, 360, "v")
    result = json.loads(
        NetworkJobs(graph, None).manage_calculation(
            context(),
            CalculationQuery("status", "saved"),
        )
    )
    assert result["id"] == "saved"
    graph.submit.assert_not_called()


def test_unsupported_frequency_is_rejected_instead_of_silently_discarded() -> None:
    with pytest.raises(ValidationError, match="frequency"):
        TypeAdapter(TransportScenario).validate_python(
            {
                "kind": "network",
                "region_ids": ["region"],
                "scenario": "road",
                "links": [
                    {
                        "action": "add",
                        "network": "intercity",
                        "mode": "rail",
                        "source": "A",
                        "target": "B",
                        "hours": 1,
                        "frequency": 10,
                    }
                ],
            }
        )
