import json
from unittest.mock import Mock

from app.adapter.chat.calculation_tools import CalculationTools
from app.usecase.graph_snapshot import GraphModelInfo


def test_capabilities_use_current_graph_metadata_instead_of_a_fixed_snapshot() -> None:
    graph = Mock()
    graph.model_info.return_value = GraphModelInfo(
        "current-artifact", "hansen-frequency-v2", "road-capacity-v1", False, 84,
    )
    result = json.loads(CalculationTools(Mock(), graph).calculation_capabilities(Mock()))
    assert result["national_road_edits"]["model"]["version"] == "current-artifact"
    assert result["national_road_edits"]["model"]["road_cost_model"] == "road-capacity-v1"
    assert result["transport_links"]["intercity_in_road"] is False
    assert result["economic_appraisal"]["available"] is True


def test_graph_calculations_are_unavailable_without_an_engine() -> None:
    result = json.loads(CalculationTools(Mock()).calculation_capabilities(Mock()))
    assert result["national_road_edits"]["available"] is False
    assert result["national_road_edits"]["model"] is None
    assert result["transport_links"]["available"] is False
    assert result["economic_appraisal"]["available"] is False
