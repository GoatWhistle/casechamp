import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pyarrow.parquet as pq
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from graph_russia import xyz


def main() -> None:
    graph = ROOT / 'data/graph_ru'
    nodes = pq.read_table(graph / 'nodes.parquet').to_pandas()
    pts = pq.read_table(graph / 'points.parquet').to_pandas()
    ways = pq.read_table(graph / 'ways.parquet', columns=['is_ferry', 'is_seasonal']).to_pandas()
    road_nodes = np.zeros(len(nodes), dtype=bool)
    allseason_nodes = np.zeros(len(nodes), dtype=bool)
    for batch in pq.ParquetFile(graph / 'edges.parquet').iter_batches(columns=['src', 'dst', 'way_idx']):
        src, dst, way = [batch.column(name).to_numpy() for name in ['src', 'dst', 'way_idx']]
        road = ~ways.is_ferry.to_numpy()[way]
        allseason = road & ~ways.is_seasonal.to_numpy()[way]
        road_nodes[src[road]] = True
        road_nodes[dst[road]] = True
        allseason_nodes[src[allseason]] = True
        allseason_nodes[dst[allseason]] = True
    seasonal = '--seasonal' in sys.argv
    positions = np.maximum(pts.node.to_numpy(), 0)
    invalid = road_nodes[positions] & ~allseason_nodes[positions] if seasonal else ~road_nodes[positions]
    flagged = pts[pts.on_road & invalid].copy()
    prefix = 'seasonal-anchors' if seasonal else 'ferry-anchors'
    candidates = np.flatnonzero(allseason_nodes)
    tree = cKDTree(xyz(nodes.lat.to_numpy()[candidates], nodes.lon.to_numpy()[candidates]))
    chord, positions = tree.query(xyz(flagged.lat.to_numpy(), flagged.lon.to_numpy()))
    flagged['candidate_node'] = candidates[positions]
    flagged['candidate_snap_km'] = 12742 * np.arcsin(np.clip(chord / 2, 0., 1.))
    flagged['candidate_within_5km'] = flagged.candidate_snap_km <= 5.
    with duckdb.connect(str(ROOT / 'data/casechamp.duckdb'), read_only=True) as con:
        names = con.sql("select oktmo point_id,object_name from stg_settlements where object_level='Населенный пункт'").df()
    flagged = flagged.merge(names, on='point_id')
    flagged.to_csv(ROOT / 'work/road-coverage' / f'{prefix}.csv', index=False)
    summary = {'anchor_kind': prefix, 'affected_points': len(flagged), 'population': int(flagged.population.sum()),
               'regions': int(flagged.region.nunique()),
               'road_candidate_within_5km': int(flagged.candidate_within_5km.sum()),
               'candidate_population': int(flagged.loc[flagged.candidate_within_5km, 'population'].sum()),
               'limitation': 'Nearest existing graph node, not all original OSM vertices. is_seasonal is legacy metadata; candidate is not yet a published route.'}
    (ROOT / 'work/road-coverage' / f'{prefix}.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(flagged.sort_values('population', ascending=False).head(15).to_string(index=False))


if __name__ == '__main__':
    main()
