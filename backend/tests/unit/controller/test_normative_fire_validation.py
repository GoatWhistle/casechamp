from typing import cast
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.controller.test_errors import RecordingLogger

from app.controller.errors import ErrorHandlers
from app.controller.normative.router import FireProfileInput, build_normative_router
from app.domain.errors import DataUnavailable
from app.usecase.normative.queries import NormativeQueries


@pytest.mark.parametrize("speed", [True, "40", 0, 201])
def test_invalid_http_speed_is_rejected_before_calculation(speed: object) -> None:
    queries = Mock(spec=NormativeQueries)
    app = FastAPI()
    ErrorHandlers(RecordingLogger()).register(app)
    app.include_router(build_normative_router(cast(NormativeQueries, queries)))
    with TestClient(app) as client:
        response = client.post(
            "/normative/assessments",
            json={
                "criterion_id": "N03",
                "fire_profile": {
                    "speed_kmh": speed,
                    "assumption": "Explicit control assumption",
                },
            },
        )
    assert response.status_code == 422
    queries.assess.assert_not_called()


def test_json_integer_speed_remains_a_valid_explicit_number() -> None:
    result = FireProfileInput.model_validate(
        {"speed_kmh": 40, "assumption": "Explicit control assumption"}
    )
    assert result.speed_kmh == 40


@pytest.mark.parametrize("basis", ["fire_objects", "settlements", None])
def test_http_preserves_explicit_basis_and_defaults_omitted_basis(basis: str | None) -> None:
    queries = Mock(spec=NormativeQueries)
    queries.assess.side_effect = DataUnavailable("No verified inputs")
    app = FastAPI()
    ErrorHandlers(RecordingLogger()).register(app)
    app.include_router(build_normative_router(cast(NormativeQueries, queries)))
    command: dict[str, object] = {"criterion_id": "N03"}
    if basis is not None:
        command["origin_basis"] = basis
    with TestClient(app) as client:
        response = client.post("/normative/assessments", json=command)
    assert response.status_code == 503
    queries.assess.assert_called_once_with("N03", [], None, basis or "settlements")


@pytest.mark.parametrize("basis", [None, "residential_references", "arbitrary", True])
def test_invalid_explicit_http_basis_is_rejected(basis: object) -> None:
    queries = Mock(spec=NormativeQueries)
    app = FastAPI()
    app.include_router(build_normative_router(cast(NormativeQueries, queries)))
    with TestClient(app) as client:
        response = client.post(
            "/normative/assessments", json={"criterion_id": "N03", "origin_basis": basis}
        )
    assert response.status_code == 422
    queries.assess.assert_not_called()
