from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient
from tests.storage import settings

from app.main import create_app
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative import ClickHouseNormativeRepository


def test_normative_catalog_and_facilities_come_from_storage() -> None:
    config = settings()
    with TestClient(create_app(config)) as client:
        catalog = client.get("/api/v1/normative/criteria")
        assert catalog.status_code == 200
        assert {row["id"] for row in catalog.json()} == {f"N{i:02}" for i in range(1, 10)}
        result = client.get("/api/v1/normative/criteria/N05/facilities")
        assert result.status_code == 200
        assert len(result.json()) >= 20
        assert all(
            row["source_url"] == "https://www.mfc45.ru/mfc-map.html" for row in result.json()
        )
        assert any(row["latitude"] is None for row in result.json())


def test_stored_population_origins_preserve_source_coverage() -> None:
    config = settings()
    repository = ClickHouseNormativeRepository(
        ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    )
    origins = repository.origins("Курганская область")
    assert len(origins) == 1235
    assert sum(origin.population or 0 for origin in origins) == 776661
    assert len({origin.id for origin in origins}) == len(origins)


def test_walking_preserves_missing_population_and_restores_distance_snapshot() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.post("/api/v1/normative/assessments", json={"criterion_id": "N04"})
        assert response.status_code == 200
        result = response.json()
        assert len(result["rows"]) > 1000
        assert result["scenario"]["unknown_population_points"] == len(result["rows"])
        assert result["scenario"]["lower_percent"] is None
        assert all(row["population"] is None and row["minutes"] is None for row in result["rows"])
        assert all(row["state"] == "unknown" for row in result["rows"])
        assert any(row["distance_metres"] is not None for row in result["rows"])
        latest = client.get("/api/v1/normative/criteria/N04/latest")
        assert latest.status_code == 200
        restored = latest.json()
        assert restored["run_id"] == result["run_id"]
        assert restored["saved_at"] == result["saved_at"]
        assert (
            restored["graph_fingerprint"] == sha256(result["graph_revision"].encode()).hexdigest()
        )
        saved_at = datetime.fromisoformat(result["saved_at"])
        assert saved_at.tzinfo == UTC
        assert abs((datetime.now(UTC) - saved_at).total_seconds()) < 60
        assert restored["rows"] == result["rows"]
        assert restored["criterion"] == result["criterion"]
        assert restored["rule_sets"] == result["rule_sets"]
        assert len(result["rule_sets"]) == 1
        assert len(result["rule_sets"][0]["checks"]) == 6
        assert all(row["rule_set_id"] == result["rule_sets"][0]["id"] for row in result["rows"])
        assert all(
            check["threshold"] is None and check["result"] == "unknown"
            for check in result["rule_sets"][0]["checks"]
        )

        assert result["model_revision"] == "normative-v8"
        point = next(
            row
            for row in result["rows"]
            if row["distance_metres"] is not None and 500 < row["distance_metres"] < 2000
        )
        route = client.get(f"/api/v1/normative/assessments/{result['run_id']}/routes/{point['id']}")
        assert route.status_code == 200
        geometry = route.json()["geometry"]
        assert abs(geometry["distance_metres"] - point["distance_metres"]) < 1e-4
        assert len(geometry["network_coordinates"]) >= 2
        assert len(geometry["approaches"]) == 2


def test_library_calculates_times_without_substituting_a_default_territory(tmp_path: Path) -> None:
    with TestClient(create_app(replace(settings(), graph_dir=tmp_path))) as client:
        response = client.post("/api/v1/normative/assessments", json={"criterion_id": "N07"})
        assert response.status_code == 200
        result = response.json()
        assert len(result["rows"]) == 1235
        assert len(result["facilities"]) == 429
        assert all(f["service"] == "library" for f in result["facilities"])
        assert all("детск" not in f["name"].lower() for f in result["facilities"])
        assert sum(f["latitude"] is None for f in result["facilities"]) == 394
        assert sum(f["published_on"] is not None for f in result["facilities"]) == 407
        assert not any(
            f["id"] in {"yugov-library-8642", "yugov-library-8075"} for f in result["facilities"]
        )
        city = next(row for row in result["rows"] if row["id"] == "37701000001")
        assert city["threshold_minutes"] == 40
        encoded = next(row for row in result["rows"] if row["id"] == "37502000101")
        assert encoded["threshold_minutes"] == 60
        assert encoded["municipality_code"] == "37502000"
        assert (
            encoded["territory_verification_status"] == "encoded_parent_2024_assignment_unconfirmed"
        )
        assert (
            encoded["territory_structure_source_url"]
            == "https://www.nalog.gov.ru/rn27/news/activities_fts/6061590/"
        )
        assert sum(row["threshold_minutes"] is not None for row in result["rows"]) == 384
        assert "territory_conditions_missing" in encoded["uncertainty"]
        assert city["territory_source_url"] == "https://www.kurgan-city.ru/city/ustav/"
        assert "facility_profile_unconfirmed" in city["uncertainty"]
        assert any(row["minutes"] is not None for row in result["rows"])
        assert all(row["state"] == "unknown" for row in result["rows"])
        assert all("transport_mode_unconfirmed" in row["uncertainty"] for row in result["rows"])
        assert any(row["threshold_minutes"] is None for row in result["rows"])
        restored = client.get("/api/v1/normative/criteria/N07/latest").json()
        assert restored["rows"] == result["rows"]
        assert restored["facilities"] == result["facilities"]


def test_fire_profile_is_explicit_and_replays_the_saved_route(tmp_path: Path) -> None:
    with TestClient(create_app(replace(settings(), graph_dir=tmp_path))) as client:
        missing = client.post("/api/v1/normative/assessments", json={"criterion_id": "N03"})
        assert missing.status_code == 422
        profile = {
            "speed_kmh": 40,
            "assumption": "Контрольный сценарий: постоянная скорость 40 км/ч, не норматив и не наблюдение",
        }
        response = client.post(
            "/api/v1/normative/assessments",
            json={
                "criterion_id": "N03",
                "fire_profile": profile,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["fire_profile"] == profile
        assert len(result["rows"]) == 1235
        assert len(result["facilities"]) == 26
        assert sum(f["latitude"] is not None for f in result["facilities"]) == 9
        assert all(f["published_on"] is None for f in result["facilities"])
        assert all("#page=" in f["source_url"] for f in result["facilities"])
        assert all(
            f["source_sha256"] == "c7710fe218bf522a93bb1af8c0653316ef5c77dea6776a9d55bb5587856ac3d4"
            for f in result["facilities"]
        )
        incomplete = next(f for f in result["facilities"] if f["id"] == "psch-34")
        assert incomplete["address"] == "г. Петухово, ул. Карла Маркса"
        assert incomplete["latitude"] is None and incomplete["coordinate_status"] == "missing"
        untouched = next(f for f in result["facilities"] if f["id"] == "psch-11")
        assert untouched["name"] == "11 ПСЧ" and untouched["latitude"] is None
        assert all(f["id"] != "psch-03" for f in result["facilities"])
        assert all(row["state"] == "unknown" for row in result["rows"])
        assert all("fire_readiness_unconfirmed" in row["uncertainty"] for row in result["rows"])
        city = next(row for row in result["rows"] if row["id"] == "37701000001")
        assert city["threshold_minutes"] == 10
        assert city["minutes"] is not None
        restored = client.get("/api/v1/normative/criteria/N03/latest").json()
        assert restored["rows"] == result["rows"]
        assert restored["fire_profile"] == profile
        assert restored["facilities"] == result["facilities"]
        route = client.get(f"/api/v1/normative/assessments/{result['run_id']}/routes/{city['id']}")
        assert route.status_code == 200
        geometry = route.json()["geometry"]
        assert abs(geometry["minutes"] - city["minutes"]) < 1e-4
        facility = next(f for f in result["facilities"] if f["id"] == city["facility_id"])
        assert geometry["approaches"][0][0] == [facility["longitude"], facility["latitude"]]
        assert geometry["approaches"][-1][-1] == [city["longitude"], city["latitude"]]


def test_medical_snapshots_keep_missing_adult_population_and_care_forms_separate(
    tmp_path: Path,
) -> None:
    with TestClient(create_app(replace(settings(), graph_dir=tmp_path))) as client:
        for key, service in [("N01", "emergency_cardiology"), ("N02", "urgent_cardiology")]:
            response = client.post("/api/v1/normative/assessments", json={"criterion_id": key})
            assert response.status_code == 200
            result = response.json()
            assert result["criterion"]["service"] == service
            assert result["model_revision"] == "normative-v8"
            assert result["qualification_as_of"] is None
            assert len(result["rows"]) == 1235
            assert all(f["service"] == service for f in result["facilities"])
            assert all(r["population"] is None and r["state"] == "unknown" for r in result["rows"])
            assert all(r["catchment_source_url"] is None for r in result["rows"])
            assert all(r["threshold_source_url"] is None for r in result["rows"])
            assert sum(r["minutes"] is not None for r in result["rows"]) == 1234
            assert result["scenario"]["lower_percent"] is None
            restored = client.get(f"/api/v1/normative/criteria/{key}/latest")
            assert restored.status_code == 200
            assert restored.json() == result
