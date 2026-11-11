import json
from unittest.mock import Mock

import pytest
from pydantic_ai import ModelRetry

from app.adapter.chat.transport_tools import TransportTools
from app.domain.appraisal_inputs import DemandScenario, PassengerFlow, ProjectAssumptions
from app.usecase.graph_snapshot import GraphModelInfo
from app.usecase.road_graph import RoadJob
from app.usecase.transport_links import LinkChange, TransportLink


def project() -> ProjectAssumptions:
    return ProjectAssumptions(
        [PassengerFlow("origin", "Market", 1000, 300, "User assumption")],
        [DemandScenario(name, 1, 1) for name in ("low", "base", "high")],
        100000, 1000, 20, 0.05, 2026, "User assumption",
    )


def test_rail_scenario_passes_economic_inputs_to_the_same_calculation() -> None:
    graph = Mock()
    link = LinkChange("add", "intercity", "rail", "Source", "Market", 1)
    assumptions = project()
    graph.submit.return_value = RoadJob(
        "rail-job", "region", "Region", "road", [], "queued", 0, 360, "current",
        links=[link], appraisal_assumptions=assumptions,
    )
    result = TransportTools(graph).recalculate_transport_links(
        Mock(), ["region"], "road", [link], appraisal=assumptions,
    )
    graph.submit.assert_called_once_with(
        "region", "road", [], [link], queue=True, appraisal=assumptions,
    )
    assert json.loads(result)[0]["id"] == "rail-job"


def test_regional_economic_inputs_are_not_reused_for_several_regions() -> None:
    graph = Mock()
    with pytest.raises(ModelRetry, match="one region"):
        TransportTools(graph).recalculate_transport_links(
            Mock(), ["one", "two"], "road",
            [LinkChange("remove", "intercity", "air", "Source", "*")],
            appraisal=project(),
        )
    graph.submit.assert_not_called()


def test_airport_closure_keeps_all_connections_in_one_joint_scenario() -> None:
    graph = Mock()
    link = LinkChange("remove", "intercity", "air", "Airport city", "*")
    graph.submit.return_value = RoadJob(
        "closure", "one", "Region", "summer", [], "queued", 0, 360, "v", links=[link],
    )
    TransportTools(graph).recalculate_transport_links(Mock(), ["one", "two"], "summer", [link])
    assert graph.submit.call_count == 2
    for call in graph.submit.call_args_list:
        assert call.args[1:] == ("summer", [], [link])
        assert call.kwargs == {"queue": True, "appraisal": None}


def test_link_listing_reports_its_snapshot_and_possible_truncation() -> None:
    graph = Mock()
    graph.transport_links.return_value = [
        TransportLink("intercity", "air", "A", "A", str(i), str(i), 2) for i in range(60)
    ]
    graph.model_info.return_value = GraphModelInfo("v", "model", "road-capacity-v1", True, 0)
    result = json.loads(TransportTools(graph).find_transport_links(Mock(), "intercity", "A"))
    assert result["possibly_truncated"] is True
    assert result["scope"] == "calculation_snapshot_not_live_service_schedule"
    assert result["model"]["intercity_in_road"] is True
