import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]


def validate(graph: Path) -> dict:
    nodes = pq.read_table(graph / 'nodes.parquet').to_pandas()
    ways = pq.read_table(graph / 'ways.parquet', columns=['way_idx', 'way_id', 'oneway', 'km', 'is_ferry', 'operating_season']).to_pandas()
    points = pq.read_table(graph / 'points.parquet').to_pandas()
    old = pq.read_table(ROOT / 'data/road-refresh/baseline/points.parquet', columns=['point_id']).column(0).to_pylist()
    assert np.array_equal(nodes.node, np.arange(len(nodes)))
    assert np.array_equal(ways.way_idx, np.arange(len(ways)))
    assert points.point_id.is_unique and set(points.point_id) == set(old)
    assert ways.way_id.is_unique
    assert set(ways.operating_season) <= {'all', 'summer', 'winter', 'unknown'}
    has_road = np.zeros(len(nodes), dtype=bool)
    edge_counts = np.zeros(len(ways), dtype=np.int64)
    edge_count = 0
    for batch in pq.ParquetFile(graph / 'edges.parquet').iter_batches():
        values = {name: batch.column(name).to_numpy() for name in batch.schema.names}
        src, dst, way = [values[name] for name in ['src', 'dst', 'way_idx']]
        assert ((src >= 0) & (src < len(nodes))).all()
        assert ((dst >= 0) & (dst < len(nodes))).all()
        assert ((way >= 0) & (way < len(ways))).all()
        assert np.isfinite(values['h']).all() and (values['h'] >= 0).all()
        assert np.isfinite(values['km']).all() and (values['km'] >= 0).all()
        np.add.at(edge_counts, way, 1)
        road = ~ways.is_ferry.to_numpy()[way]
        has_road[src[road]] = True
        has_road[dst[road]] = True
        edge_count += len(src)
    attached = points[points.on_road]
    assert (attached.node >= 0).all() and (attached.node < len(nodes)).all()
    assert (attached.snap_km <= 5.).all()
    assert has_road[attached.node].all(), 'Settlement anchored only to a ferry or an edgeless way'
    assert (points.loc[~points.on_road, 'node'] == -1).all()
    assert (edge_counts > 0).all(), 'A source way lost every edge'
    report = {'nodes': len(nodes), 'ways': len(ways), 'edges': edge_count,
              'points': len(points), 'attached_points': len(attached),
              'unbound_points': int((~points.on_road).sum()),
              'unbound_population': int(points.loc[~points.on_road, 'population'].sum()),
              'reverse_ways': int((ways.oneway == '-1').sum()),
              'ferry_only_anchors': 0, 'edgeless_ways': 0,
              'limitation': 'Structural graph checks; do not establish field road completeness.'}
    (graph / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return report


if __name__ == '__main__':
    validate(ROOT / 'data/road-refresh/graph')
