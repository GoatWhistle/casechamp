from fastapi.testclient import TestClient
from tests.storage import settings

from app.main import create_app


def test_national_inventory_is_loaded_from_storage_and_does_not_claim_cardiology() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/normative/regions/45000000/catalog/N01")
        assert response.status_code == 200
        result = response.json()
        assert result["region_id"] == "45000000"
        assert result["candidate_count"] > 100
        assert len(result["facilities"]) == result["candidate_count"]
        assert result["calculation_available"] is False
        assert result["profile_verification"] == "unconfirmed"
        assert all(f["service"] == "medical" for f in result["facilities"])
        assert all(
            f["coordinate_snapshot_sha256"] == f["source_sha256"] for f in result["facilities"]
        )
        assert all(
            f["coordinate_source"].startswith("https://www.openstreetmap.org/")
            for f in result["facilities"]
        )
