import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from artifacts import file_record, write_json
from graph_russia import haversine_km, xyz

OUT = ROOT / 'data/road-refresh/reverse'
GRAPH = ROOT / 'data/graph_ru'


def main() -> None:
    source = ET.parse(OUT / 'reverse.osm').getroot()
    coordinates = {int(row.attrib['id']): (float(row.attrib['lat']), float(row.attrib['lon']))
                   for row in source.findall('node')}
    nodes = pq.read_table(GRAPH / 'nodes.parquet').to_pandas()
    osm_ids = nodes.osm_node.to_numpy()
    assert np.all(osm_ids[:-1] <= osm_ids[1:])
    ways = pq.read_table(GRAPH / 'ways.parquet').to_pandas()
    ways = ways[(ways.oneway == '-1') & (ways.km == 0)].set_index('way_id')
    pts = pq.read_table(GRAPH / 'points.parquet').to_pandas()
    tree = cKDTree(xyz(pts.lat.to_numpy(), pts.lon.to_numpy()))
    parent = np.arange(int(nodes.comp.max()) + 1)

    def root(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = int(parent[value])
        return value

    edges, details, excluded = [], [], []
    for way in source.findall('way'):
        identifier = int(way.attrib['id'])
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in way.findall('tag')}
        ids = np.array([int(nd.attrib['ref']) for nd in way.findall('nd')], dtype=np.int64)
        if identifier not in ways.index or len(ids) < 2 or tags.get('oneway') != '-1':
            excluded.append({'way_id': identifier, 'reason': 'source_changed_or_deleted'})
            continue
        positions = np.searchsorted(osm_ids, ids)
        valid = positions < len(osm_ids)
        valid &= osm_ids[np.minimum(positions, len(osm_ids) - 1)] == ids
        junctions = np.flatnonzero(valid)
        if len(junctions) < 2 or junctions[0] != 0 or junctions[-1] != len(ids) - 1:
            excluded.append({'way_id': identifier, 'reason': 'endpoints_missing_from_old_graph'})
            continue
        lat, lon = np.array([coordinates[int(identifier)] for identifier in ids]).T
        mapped = positions[junctions]
        error = haversine_km(lat[junctions], lon[junctions], nodes.lat.to_numpy()[mapped], nodes.lon.to_numpy()[mapped])
        if np.max(error) > .05:
            excluded.append({'way_id': identifier, 'reason': 'junction_moved_over_50m'})
            continue
        cumulative = np.r_[0., np.cumsum(haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:]))]
        attrs = ways.loc[identifier]
        for a, b in zip(junctions[:-1], junctions[1:]):
            distance = float(cumulative[b] - cumulative[a])
            edges.append({'src': int(positions[b]), 'dst': int(positions[a]),
                          'h': distance / float(attrs.speed_kmh), 'km': distance,
                          'way_idx': int(attrs.way_idx)})
            first, second = root(int(nodes.comp.iloc[positions[a]])), root(int(nodes.comp.iloc[positions[b]]))
            parent[second] = first
        _, nearest = tree.query(xyz(np.array([lat[0]]), np.array([lon[0]])))
        details.append({'way_id': identifier, 'way_idx': int(attrs.way_idx), 'km': float(cumulative[-1]),
                        'nearest_settlement_region': pts.region.iloc[int(nearest[0])],
                        'name': tags.get('name'), 'segments': len(junctions) - 1})
    schema = pq.read_schema(GRAPH / 'edges.parquet')
    pq.write_table(pa.Table.from_pylist(edges, schema=schema), OUT / 'recovered-edges.parquet')
    roots = np.array([root(index) for index in range(len(parent))])
    with duckdb.connect(str(ROOT / 'data/casechamp.duckdb'), read_only=True) as con:
        markets = con.sql('select node from market_cities').fetchnumpy()['node']
        names = con.sql("select oktmo point_id, object_name from stg_settlements where object_level='Населенный пункт'").df()
    valid_markets = markets[(markets >= 0) & (markets < len(nodes))]
    market_components = nodes.comp.to_numpy()[valid_markets]
    before = np.isin(pts.comp.to_numpy(), market_components) & pts.on_road.to_numpy()
    after = np.isin(roots[np.maximum(pts.comp.to_numpy(), 0)], roots[market_components]) & pts.on_road.to_numpy()
    gained = pts[after & ~before].merge(names, on='point_id')
    gained.to_csv(ROOT / 'work/road-coverage/reverse-restored-settlements.csv', index=False)
    report = {'restored_ways': len(details), 'restored_edges': len(edges),
              'restored_km': sum(row['km'] for row in details),
              'settlements_gaining_market_component': len(gained),
              'population_gaining_market_component': int(gained.population.sum()),
              'ways': details, 'excluded': excluded,
              'source': file_record(OUT / 'reverse.osm'),
              'output': file_record(OUT / 'recovered-edges.parquet'),
              'limitation': 'Topology of the unfiltered legacy graph only; no seasonal index or new snapping recalculated.'}
    write_json(ROOT / 'work/road-coverage/reverse-recovery.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in {'ways', 'source', 'output'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
