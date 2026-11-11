from unittest.mock import Mock

from app.repository.clickhouse.atlas import ClickHouseAtlasRepository


def test_point_lookup_uses_a_bound_id_and_covers_settlements_outside_link_nodes() -> None:
    reader = Mock()
    reader.rows.return_value = [{
        "id": "point", "name": "Town", "region_id": "01000000",
        "lat": 45., "lon": 42., "x": 1., "y": 2.,
    }]
    point = ClickHouseAtlasRepository(reader).point("point")
    assert point is not None and point.lat == 45 and point.lon == 42
    sql, parameters = reader.rows.call_args.args
    assert "plexus_atlas.atlas_settlements" in sql
    assert "plexus_graph.locations" in sql
    assert parameters == {"id": "point"}
    reader.rows.return_value = []
    assert ClickHouseAtlasRepository(reader).point("missing") is None
