from typing import cast
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.controller.test_errors import RecordingLogger
from tests.unit.usecase.test_regional_index_modes import evaluate

from app.controller.errors import ErrorHandlers
from app.controller.normative.indices import build_regional_indices_router
from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.normative.index_map import IndexMapQueries, IndexMapRegion
from app.usecase.normative.indices import RegionalIndices


def client(queries: Mock, maps: Mock) -> TestClient:
    app = FastAPI()
    ErrorHandlers(RecordingLogger()).register(app)
    app.include_router(
        build_regional_indices_router(cast(RegionalIndices, queries), cast(IndexMapQueries, maps))
    )
    return TestClient(app)


def test_walking_index_http_preserves_thresholds_units_and_unknown_population() -> None:
    queries, maps = Mock(spec=RegionalIndices), Mock(spec=IndexMapQueries)
    queries.latest.return_value = evaluate("walk")
    with client(queries, maps) as api:
        response = api.get("/normative/regions/R/indices/N04")
    assert response.status_code == 200
    row = response.json()
    assert row["basis"]["unit"] == "metres"
    assert row["basis"]["thresholds"] == [500, 800]
    assert [value["point_share_percent"] for value in row["scenario"]] == [0, 100]
    assert all(value["population_share_percent"] is None for value in row["scenario"])
    assert row["legal_compliance_confirmed"] is False
    assert row["measurement_definition"] == "single_reference_point"


def test_map_http_keeps_missing_measurement_null_and_only_returns_stored_regions() -> None:
    queries, maps = Mock(spec=RegionalIndices), Mock(spec=IndexMapQueries)
    maps.regions.return_value = [
        IndexMapRegion(
            "07000000",
            "Stored region",
            None,
            None,
            "reference_points",
            "measurement_missing",
            None,
            None,
            60,
            60,
            "minutes",
            None,
            None,
        )
    ]
    with client(queries, maps) as api:
        response = api.get("/normative/indices/N01/regions?stage=baseline")
    assert response.status_code == 200
    rows = response.json()
    assert [row["region_id"] for row in rows] == ["07000000"]
    assert rows[0]["value_min"] is rows[0]["value_max"] is None
    assert rows[0]["legal_compliance_confirmed"] is False
    maps.regions.assert_called_once_with("N01", "baseline")


@pytest.mark.parametrize(
    "error,status",
    [(DataUnavailable("Missing normative tables"), 503), (InvalidQuery("Unknown region"), 422)],
)
def test_index_errors_are_not_serialized_as_zero_coverage(error: Exception, status: int) -> None:
    queries, maps = Mock(spec=RegionalIndices), Mock(spec=IndexMapQueries)
    queries.latest.side_effect = error
    with client(queries, maps) as api:
        response = api.get("/normative/regions/R/indices/N01")
    assert response.status_code == status
    assert "scenario" not in response.json()
