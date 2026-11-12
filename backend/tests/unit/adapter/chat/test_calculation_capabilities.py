import json
from unittest.mock import Mock

from app.adapter.chat.calculation_tools import CalculationTools
from app.usecase.graph_snapshot import GraphModelInfo


def test_capabilities_use_current_graph_metadata_instead_of_a_fixed_snapshot() -> None:
    graph = Mock()
    graph.model_info.return_value = GraphModelInfo(
        "current-artifact",
        "hansen-frequency-v2",
        "road-capacity-v1",
        False,
        84,
    )
    result = json.loads(CalculationTools(Mock(), graph).calculation_capabilities(Mock()))
    assert result["transport_model"]["model"]["version"] == "current-artifact"
    assert result["transport_model"]["model"]["road_cost_model"] == "road-capacity-v1"
    assert result["transport_links"]["intercity_in_road"] is False
    assert result["economic_appraisal"]["available"] is True


def test_graph_calculations_are_unavailable_without_an_engine() -> None:
    result = json.loads(CalculationTools(Mock()).calculation_capabilities(Mock()))
    assert result["transport_model"]["available"] is False
    assert result["transport_model"]["model"] is None
    assert result["transport_links"]["available"] is False
    assert result["economic_appraisal"]["available"] is False


def test_development_has_one_adaptive_objective_interface() -> None:
    result = json.loads(CalculationTools(Mock(), traffic=Mock()).calculation_capabilities(Mock()))
    development = result["road_development"]
    assert development["available"] is True
    assert development["objectives"] == ["connectivity", "transit", "congestion"]
    assert development["default_objective"] == "connectivity"
    assert "focus_bounds" in development
    assert "automatic_road_analysis" not in result
    assert "new_connections" not in result
    assert "regional_sensitivity" not in result
    assert "traffic" not in result["settlement_connectivity"]
    assert "speed_change" not in result["named_road_corridors"]
    assert "speed_baseline" not in result["named_road_corridors"]
