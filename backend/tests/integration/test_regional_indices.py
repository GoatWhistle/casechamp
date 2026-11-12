import pytest
from fastapi.testclient import TestClient
from tests.storage import settings

from app.main import create_app


def test_index_recomputes_the_saved_reference_share_and_does_not_claim_population_coverage() -> (
    None
):
    with TestClient(create_app(settings())) as client:
        measurement = client.get("/api/v1/normative/regions/81000000/measurements/N01/latest")
        assert measurement.status_code == 200
        saved = measurement.json()
        response = client.get("/api/v1/normative/regions/81000000/indices/N01")
        assert response.status_code == 200
        index = response.json()
        assert index["run_id"] == saved["run_id"]
        assert index["basis"]["thresholds"] == [60]
        value = index["scenario"][0]
        expected = sum(row["minutes"] is not None and row["minutes"] <= 60 for row in saved["rows"])
        assert value["point_share_percent"] == pytest.approx(100 * expected / len(saved["rows"]))
        assert value["within_points"] == expected
        assert value["population_share_percent"] is None
        assert index["legal_compliance_confirmed"] is False
        assert index["qualification"] == "conditional_known_objects"


def test_kurgan_regional_threshold_is_not_exported_to_moscow_and_unknown_region_is_rejected() -> (
    None
):
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/normative/regions/45000000/indices/N05")
        assert response.status_code == 200
        assert response.json()["basis"] is None
        assert response.json()["scenario"] == []
        assert client.get("/api/v1/normative/regions/unknown/indices/N01").status_code == 422
