import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.sparse.csgraph import connected_components, dijkstra

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from graphlib import build_csr


def main() -> None:
    graph = ROOT / 'data/graph_ru'
    ways = pq.read_table(graph / 'ways.parquet', columns=['is_ferry', 'is_seasonal'])
    allowed = ~(ways['is_ferry'].to_numpy() | ways['is_seasonal'].to_numpy())
    edges = pq.read_table(graph / 'edges.parquet')
    keep = allowed[edges['way_idx'].to_numpy()]
    src, dst, weight = [edges[column].to_numpy()[keep] for column in ['src', 'dst', 'h']]
    n = pq.read_metadata(graph / 'nodes.parquet').num_rows
    matrix = build_csr(src, dst, weight, n, undirected=True).astype(np.float64)
    del src, dst, weight, edges, keep
    _, components = connected_components(matrix, directed=False)
    flagged = pd.read_csv(ROOT / 'work/road-coverage/ferry-anchors.csv', dtype={'point_id': str})
    with duckdb.connect(str(ROOT / 'data/casechamp.duckdb'), read_only=True) as con:
        markets = con.sql('select city,node from market_cities').df()
    target_nodes = markets.node.to_numpy()
    target_nodes = target_nodes[(target_nodes >= 0) & (target_nodes < n)]
    market_components = components[target_nodes]
    flagged['old_base_reachable'] = np.isin(components[flagged.node], market_components)
    flagged['new_base_reachable'] = flagged.candidate_within_5km & np.isin(components[flagged.candidate_node], market_components)
    assert not flagged.old_base_reachable.any()
    distance = dijkstra(matrix, directed=False, indices=int(markets[markets.city == 'Омск'].node.iloc[0]))
    flagged['candidate_hours_to_omsk'] = distance[flagged.candidate_node] + flagged.candidate_snap_km / 15.
    flagged['old_hours_to_omsk'] = distance[flagged.node] + flagged.snap_km / 15.
    flagged.to_csv(ROOT / 'work/road-coverage/ferry-anchors-verified.csv', index=False)
    summary = {
        'new_base_reachable_points': int(flagged.new_base_reachable.sum()),
        'new_base_reachable_population': int(flagged.loc[flagged.new_base_reachable, 'population'].sum()),
        'omsk_examples': flagged[flagged.point_id.isin(['52603151051', '52657432101'])][
            ['point_id', 'object_name', 'candidate_snap_km', 'candidate_hours_to_omsk']].to_dict('records'),
        'filter': 'Exclude legacy is_ferry and is_seasonal; undirected national road model',
        'limitation': 'Model path, not field verification; not a published Hansen recalculation.',
    }
    (ROOT / 'work/road-coverage/ferry-anchors-verified.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
