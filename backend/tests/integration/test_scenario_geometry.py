from pathlib import Path

from tests.storage import atlas_repository

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.selection_geometry import selection_geometry
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot


def test_scenario_geometry_reads_complete_osm_ways_without_viewport_sampling() -> None:
    reader = atlas_repository().reader
    data = GraphData(Path("data"), ClickHouseGraphSnapshot(reader))
    way_ids = [98777273, 113693623, 113693624]
    geometry = selection_geometry(data, way_ids)
    expected = reader.rows(
        "SELECT sum(km) AS km FROM plexus_graph.ways WHERE way_id IN {ids:Array(Int64)}",
        {"ids": way_ids},
    )[0]
    line_count = reader.rows(
        "SELECT count() AS count FROM plexus_graph.road_lines WHERE way_id IN {ids:Array(Int64)}",
        {"ids": way_ids},
    )[0]
    assert abs(geometry.length_km - float(expected["km"])) < 1e-6
    assert len(geometry.lines) == line_count["count"] > 0
    assert geometry.names
    assert all(len(line) >= 2 for line in geometry.lines)
