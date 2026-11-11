from tests.storage import settings

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot


def test_resolved_capitals_have_existing_market_road_attachments() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    snapshot = ClickHouseGraphSnapshot(reader)
    for name in ("Москва, Москва", "Санкт-Петербург, Санкт-Петербург"):
        places = snapshot.read("corridor_places", {"query": name})
        assert len(places) == 1
        point = str(places[0][0])
        attachments = snapshot.read("route_points", {"points": [point]})
        assert len(attachments) == 1
        market = reader.rows(
            "SELECT node,snap_h FROM plexus_casechamp.market_cities WHERE oktmo={id:String}",
            {"id": point},
        )[0]
        assert attachments[0] == (point, market["node"], market["snap_h"] * 15)
        assert attachments[0][1] >= 0
