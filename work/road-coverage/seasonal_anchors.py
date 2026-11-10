import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / 'data/road-refresh/graph'


def xyz(lat, lon):
    a, b = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(a) * np.cos(b), np.cos(a) * np.sin(b), np.sin(a)]


def main():
    nodes = pq.read_table(GRAPH / 'nodes.parquet', columns=['lat', 'lon']).to_pandas()
    ways = pq.read_table(GRAPH / 'ways.parquet', columns=['operating_season', 'is_ferry']).to_pandas()
    points = pq.read_table(GRAPH / 'points.parquet').to_pandas()
    permanent = np.zeros(len(nodes), dtype=bool)
    allowed = ((ways.operating_season == 'all') & ~ways.is_ferry).to_numpy()
    for batch in pq.ParquetFile(GRAPH / 'edges.parquet').iter_batches(columns=['src', 'dst', 'way_idx']):
        keep = allowed[batch.column('way_idx').to_numpy()]
        permanent[batch.column('src').to_numpy()[keep]] = True
        permanent[batch.column('dst').to_numpy()[keep]] = True
    selected = points[points.on_road & ~permanent[np.maximum(points.node, 0)]].copy()
    selected = selected[~selected.region.isin(['Москва', 'Санкт-Петербург', 'Севастополь'])]
    ids = np.flatnonzero(permanent)
    tree = cKDTree(xyz(nodes.lat.to_numpy()[ids], nodes.lon.to_numpy()[ids]))
    chord, nearest = tree.query(xyz(selected.lat, selected.lon))
    selected['permanent_node'] = ids[nearest]
    selected['permanent_snap_km'] = 12742 * np.arcsin(np.clip(chord / 2, 0, 1))
    selected.to_csv(Path(__file__).with_name('seasonal-anchors.csv'), index=False)
    near = selected[selected.permanent_snap_km <= 5]
    report = dict(seasonal_only_anchor_points=len(selected), population=int(selected.population.sum()),
                  with_permanent_node_within_5km=len(near), nearby_population=int(near.population.sum()))
    Path(__file__).with_name('seasonal-anchors.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report)


if __name__ == '__main__':
    main()
