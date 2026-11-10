import pytest
from httpx2 import ASGITransport, AsyncClient
from tests.storage import settings

from app.main import create_app
from app.repository.clickhouse.accessibility import ClickHouseAccessibilityRepository
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.accessibility import AccessibilityQueries


@pytest.mark.anyio
async def test_persisted_comparison_is_exposed_without_changing_published_index() -> None:
    app = create_app(settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        before = (await client.get("/api/v1/regions/18000000?season=summer")).json()
        response = await client.get("/api/v1/regions/18000000/accessibility")
        assert response.status_code == 200
        body = response.json()
        assert len(body["rows"]) == 2
        assert body["run"]["model_version"] == "hansen-planned-v1"
        assert all(row["scheduled_index"] is None for row in body["rows"])
        invalid = await client.get("/api/v1/regions/18000000/accessibility?half_life=3")
        assert invalid.status_code == 422
        missing = await client.get("/api/v1/regions/00000000/accessibility")
        assert missing.status_code == 404
        after = (await client.get("/api/v1/regions/18000000?season=summer")).json()
        assert before["hansen"] == after["hansen"]


def test_all_regions_have_finite_comparisons_and_nonnegative_removal_effects() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    atlas = ClickHouseAtlasRepository(reader)
    queries = AccessibilityQueries(ClickHouseAccessibilityRepository(reader), atlas)
    for region in atlas.regions():
        result = queries.compare(region.id, 2)
        for row in result.rows:
            assert row.previous >= 0
            assert row.potential >= 0
            assert row.without_air <= row.potential + 1e-5
            assert row.without_rail <= row.potential + 1e-5
            assert row.without_water <= row.potential + 1e-5
            assert 0 <= row.population_coverage <= 1
