import json
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic_ai import ModelRetry

from app.adapter.chat.municipal_tools import MunicipalTools
from app.controller.municipalities.access import build_municipal_access_router
from app.domain.errors import DataUnavailable
from app.usecase.municipal_access import MunicipalAccessResult
from app.usecase.municipal_scenarios import MunicipalTrafficBaseline, MunicipalTrafficCorridor
from app.usecase.traffic import TrafficJob, TrafficScope


def test_agent_and_http_return_same_accessibility_detail() -> None:
    access = Mock()
    access.run.return_value = MunicipalAccessResult(
        "region", "district", "N01", "sha", "run", "today", "minutes", "car", 60.,
        12, 10, 1, 1, 3, 90., 120., [], 3, 0, 10,
    )
    app = FastAPI()
    app.include_router(build_municipal_access_router(access))
    response = TestClient(app).get("/regions/region/municipalities/district/access",
                                  params={"criterion_id": "N01", "limit": 10})
    agent = MunicipalTools(Mock(), None, access)
    context = Mock()
    context.deps.pending = []
    result = json.loads(agent.municipal_analysis(context, "access", "region", "district",
                                                 criterion_id="N01"))
    assert context.deps.pending[0].type == "map"
    assert context.deps.pending[0].map.municipal_access.threshold == 60.
    assert context.deps.pending[0].map.municipal_access.municipality_id == "district"
    assert response.status_code == 200
    assert response.json() == result
    assert result["unreachable_points"] == 1
    assert result["legal_compliance_confirmed"] is False


def test_agent_reports_missing_measurements_without_fabricating_result() -> None:
    access = Mock()
    access.run.side_effect = DataUnavailable("Missing measurements")
    with pytest.raises(ModelRetry, match="Missing measurements"):
        MunicipalTools(Mock(), None, access).municipal_analysis(
            Mock(), "access", "region", "district", criterion_id="N01",
        )


def test_agent_preserves_corridor_restrictions_and_emits_baseline_map() -> None:
    scenarios = Mock()
    view = TrafficJob("baseline", TrafficScope(), status="completed")
    scenarios.baseline.return_value = MunicipalTrafficBaseline(
        "published", "district", [MunicipalTrafficCorridor(
            10, 2., 100., 3., capacity_eligible=False,
            capacity_reason="disconnected_segments", connected_parts=2,
        )], [], 0.001, None, "sha", view,
    )
    context = Mock()
    context.deps.pending = []
    result = json.loads(MunicipalTools(Mock(), scenarios).municipal_analysis(
        context, "baseline", "region", "district",
    ))
    assert result["corridors"][0]["capacity_eligible"] is False
    assert result["corridors"][0]["capacity_reason"] == "disconnected_segments"
    assert result["corridors"][0]["connected_parts"] == 2
    assert result["baseline_id"] == "published"
    assert "roads" not in result and "view" not in result
    assert context.deps.pending[0].traffic == view
