from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from normative_walking.regional_assembly import assemble


def raw_source(path: Path, longitude: float = 65.0) -> Path:
    path.mkdir()
    pq.write_table(pa.table({'osm_id': [100, 200, 300], 'latitude': [55.0, 55.001, 55.002], 'longitude': [65.0, longitude, 65.0]}), path / 'nodes.parquet')
    pq.write_table(pa.table({'source': [100, 200], 'target': [200, 300], 'metres': [111.0, 112.0], 'way_id': [1, 2]}), path / 'edges.parquet')
    pq.write_table(pa.table({'id': ['osm-way-5'], 'name': ['Home'], 'latitude': [55.0], 'longitude': [65.0],
                            'coordinate_source': ['https://www.openstreetmap.org/way/5'], 'origin_type': ['residential_building_reference']}), path / 'origins.parquet')
    return path


def test_shared_source_nodes_edges_and_homes_are_deduplicated_without_adding_reverse_edges(tmp_path: Path) -> None:
    inputs = [raw_source(tmp_path / 'one'), raw_source(tmp_path / 'two')]
    output = tmp_path / 'output'
    output.mkdir()
    result = assemble(inputs, output, 'revision')
    assert result['nodes'] == 3
    assert result['edges'] == 2
    assert result['residential_buildings'] == 1
    edges = pq.read_table(output / 'edges.parquet').to_pylist()
    assert [(row['source'], row['target']) for row in edges] == [(0, 1), (1, 2)]
    assert [row['metres'] for row in edges] == [111, 112]


def test_conflicting_node_geometries_are_excluded_with_incident_edges(tmp_path: Path) -> None:
    inputs = [raw_source(tmp_path / 'one'), raw_source(tmp_path / 'two', longitude=65.01)]
    output = tmp_path / 'output'
    output.mkdir()
    result = assemble(inputs, output, 'revision')
    assert result['nodes'] == 2
    assert result['edges'] == 0
    assert result['conflicting_nodes_excluded'] == 1
    assert result['residential_buildings'] == 1
