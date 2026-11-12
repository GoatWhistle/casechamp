import pytest
from pydantic import TypeAdapter, ValidationError

from app.adapter.chat.scenario_requests import AnalysisScenario, TransportScenario


def test_road_analysis_tool_only_accepts_criticality() -> None:
    adapter = TypeAdapter(AnalysisScenario)
    request = adapter.validate_python(
        {"kind": "road_analysis", "region_id": "1", "mode": "criticality"}
    )
    assert request.mode == "criticality"
    with pytest.raises(ValidationError):
        adapter.validate_python({"kind": "road_analysis", "region_id": "1", "mode": "improvement"})


def test_agent_cannot_create_raw_direct_road_connection() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(TransportScenario).validate_python(
            {
                "kind": "connection",
                "region_id": "1",
                "source_node": 10,
                "target_node": 20,
                "travel_hours": 0.1,
            }
        )
