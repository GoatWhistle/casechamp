from fastapi.testclient import TestClient
from tests.storage import settings

from app.main import create_app


def test_medical_directory_preserves_independent_care_forms_and_missing_coordinates() -> None:
    with TestClient(create_app(settings())) as client:
        for criterion in ("N01", "N02"):
            response = client.get(f"/api/v1/normative/criteria/{criterion}/facilities")
            assert response.status_code == 200
            facilities = response.json()
            assert len(facilities) == 16
            assert sum(f["latitude"] is not None for f in facilities) == 7
            assert all(
                f["source_sha256"] == "df1f8198bc0230f40d45a8483b9a2060962cdad5293daddca3b15c71016de2c9"
                for f in facilities
            )
            assert all(f["observed_at"] == "2026-11-12" for f in facilities)
            assert all(f["published_on"] is None for f in facilities)
            assert "shadrinsk-district-hospital" not in {f["id"] for f in facilities}
            hospital = next(f for f in facilities if f["id"] == "interdistrict-hospital-1")
            assert hospital["latitude"] is None and hospital["longitude"] is None
            assert hospital["coordinate_status"] == "missing"
            assert hospital["source_url"].endswith("#page=12")
            assert hospital["address"] == "Макушино, Красная Площадь, 2"
            matched = next(f for f in facilities if f["id"] == "interdistrict-hospital-3")
            assert matched["coordinate_source"] == "https://www.openstreetmap.org/way/72226801"
            assert matched["coordinate_status"] == "geocoded_building"
            assert matched["latitude"] is not None
            assert matched["coordinate_snapshot_sha256"] == "8fb994e69910d29708416000cb718a9843a02576f5c45c1cc8e009fcb2d7f87c"
            assert matched["coordinate_snapshot_url"].endswith("kurgan_oblast-latest.osm.pbf")
            original = next(f for f in facilities if f["id"] == "kokb")
            assert original["coordinate_snapshot_sha256"] is None
