import json

import osmium
import pyarrow.parquet as pq
from synthetic_traffic.regional_pedestrian import prepare_pedestrian


def test_actual_foot_graph_preserves_access_rules_and_filters_residential_region(
    tmp_path,
):
    path = tmp_path / "source.osm.pbf"
    header = osmium.io.Header()
    header.set("osmosis_replication_timestamp", "2026-11-11T00:00:00Z")
    with osmium.SimpleWriter(str(path), header=header) as writer:
        for identifier, point in enumerate(
            [
                (0.001, 0.001),
                (0.002, 0.001),
                (0.002, 0.002),
                (1.0, 1.0),
                (1.001, 1.0),
                (1.001, 1.001),
            ],
            1,
        ):
            writer.add_node(osmium.osm.mutable.Node(id=identifier, location=point))
        writer.add_way(
            osmium.osm.mutable.Way(id=10, nodes=[1, 2, 3], tags={"highway": "footway"})
        )
        writer.add_way(
            osmium.osm.mutable.Way(
                id=11, nodes=[3, 4], tags={"highway": "service", "foot": "no"}
            )
        )
        writer.add_way(
            osmium.osm.mutable.Way(
                id=20, nodes=[1, 2, 3, 1], tags={"building": "house"}
            )
        )
        writer.add_way(
            osmium.osm.mutable.Way(
                id=21, nodes=[4, 5, 6, 4], tags={"building": "house"}
            )
        )
    region = {
        "id": "region",
        "name": "Region",
        "polygons": [[[[0, 0], [0.01, 0], [0.01, 0.01], [0, 0.01], [0, 0]]]],
    }
    metadata = prepare_pedestrian(
        path, "https://example.org/source.osm.pbf", region, tmp_path / "output"
    )
    folder = tmp_path / "output" / metadata["revision"]
    assert metadata["node_count"] == 3
    assert metadata["edge_count"] == 4
    assert metadata["origin_count"] == 1
    assert metadata["excluded_counts"]["excluded_way"] == 1
    assert (
        metadata["excluded_counts"]["residential_origins_outside_selected_region"] == 1
    )
    assert pq.read_table(folder / "origins.parquet")["id"].to_pylist() == ["osm-way-20"]
    assert (
        json.loads((folder / "manifest.json").read_text())["source_timestamp"]
        == "2026-11-11T00:00:00Z"
    )
