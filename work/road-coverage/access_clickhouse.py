import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'etl'), str(ROOT / 'backend/src')]
from app.repository.clickhouse.client import ClickHouseReader
import access_russia

GRAPH = ROOT / 'data/road-refresh/graph'
ORIGINAL_TABLE = pq.read_table
ORIGINAL_METADATA = pq.read_metadata
READER = ClickHouseReader(os.environ['CLICKHOUSE_URL'], os.environ['CLICKHOUSE_USER'], os.environ['CLICKHOUSE_PASSWORD'])


def graph_name(path):
    path = Path(path)
    if path.parent.resolve() == GRAPH.resolve() and path.stem in {'nodes', 'edges', 'ways', 'points'}:
        return path.stem
    return None


def read_table(path, columns=None, **kwargs):
    name = graph_name(path)
    if name is None or Path(path).exists():
        return ORIGINAL_TABLE(path, columns=columns, **kwargs)
    fields = '*' if columns is None else ','.join('`' + column + '`' for column in columns)
    order = {'nodes': 'node', 'edges': 'way_idx,src,dst', 'ways': 'way_idx', 'points': 'point_id'}[name]
    return READER.arrow(f'SELECT {fields} FROM plexus_refresh_graph.{name} ORDER BY {order}', {})


def read_metadata(path, **kwargs):
    name = graph_name(path)
    if name is None or Path(path).exists():
        return ORIGINAL_METADATA(path, **kwargs)
    row = READER.rows(f'SELECT count() n FROM plexus_refresh_graph.{name}', {})[0]
    return SimpleNamespace(num_rows=row['n'])


if __name__ == '__main__':
    expected = json.loads((GRAPH / 'manifest.json').read_text())['rows']
    for name, count in expected.items():
        assert READER.rows(f'SELECT count() n FROM plexus_refresh_graph.{name}', {})[0]['n'] == count
    pq.read_table = read_table
    pq.read_metadata = read_metadata
    access_russia.main()
