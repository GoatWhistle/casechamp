import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from scipy.sparse.csgraph import dijkstra

sys.path[:0] = ['etl', 'backend/src']
from graphlib import build_csr
from app.domain.pilot_routing import route
from app.repository.files.pilots import pilot_record

root = Path('data/pilot_graph_build')
source = pq.read_table(root / 'edges.parquet').to_pandas()
ways = pq.read_table(root / 'ways.parquet').to_pandas()
points = pq.read_table(root / 'points.parquet').to_pandas().set_index('point_id')
pilot = pilot_record(json.loads(Path('frontend/atlas/public/pilots/tuva.json').read_text()))
n = pq.read_metadata(root / 'nodes.parquet').num_rows
ids = [p.id for p in pilot.points if p.id in points.index and points.loc[p.id, 'on_road']]
terminals = points.loc[ids]
lookup = {v: i for i, v in enumerate(ids)}
for season in ('summer', 'winter'):
    for closed in (False, True):
        allowed = ways.operating_season.isin(['all', season]).to_numpy().copy()
        if closed:
            allowed &= ways.way_id.ne(316392825).to_numpy()
        subset = source[allowed[source.way_idx.to_numpy()]]
        graph = build_csr(subset.src.to_numpy(), subset.dst.to_numpy(), subset.h.to_numpy(), n)
        distances = dijkstra(graph, directed=True, indices=terminals.node.to_numpy())
        transformed = []
        comparisons = []
        for edge in pilot.edges:
            if edge.mode != 'road' or season not in edge.seasons:
                transformed.append(edge)
                continue
            a, b = points.loc[edge.from_id], points.loc[edge.to_id]
            value = distances[lookup[edge.from_id], int(b.node)]
            if np.isfinite(value):
                value = float(value + (a.snap_km + b.snap_km) / 15)
                transformed.append(replace(edge, travel_h=value))
            comparisons.append({'edge': edge.id, 'before': edge.travel_h, 'after': float(value) if np.isfinite(value) else None})
        if not closed:
            assert all(x['after'] is not None and abs(x['after'] - x['before']) < 1e-8 for x in comparisons)
        for frequency in (2, 4, 7):
            modified = tuple(replace(e, frequency_per_week=frequency) if e.id == 'manual:0' else e for e in transformed)
            for pair in pilot.pairs:
                result = route(modified, pair, season)
                print(json.dumps({'season': season, 'way_closed': closed, 'frequency': frequency, 'pair': pair.id, 'status': result.status, 'hours': result.total_h, 'route': result.edge_ids}, ensure_ascii=False))
        if closed:
            print(json.dumps({'season': season, 'roads_before': len(comparisons), 'unreachable_after': [x['edge'] for x in comparisons if x['after'] is None], 'changed_finite': [x for x in comparisons if x['after'] is not None and abs(x['after'] - x['before']) > 1e-8]}, ensure_ascii=False))
