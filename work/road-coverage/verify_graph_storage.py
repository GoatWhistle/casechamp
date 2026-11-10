import json
import math
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl/analytics'))
from client import ClickHouse

GRAPH = ROOT / 'data/road-refresh/graph'
COLUMNS = {'nodes': ['node','osm_node','lat','lon','comp'], 'edges': ['src','dst','way_idx','h','km'],
           'ways': ['way_idx','way_id','speed_kmh','km'], 'points': ['node','lat','lon','population','snap_km']}


def main():
    client = ClickHouse()
    result = []
    with duckdb.connect() as con:
        for name, columns in COLUMNS.items():
            expressions = ['count(*) n'] + [f'{agg}({column}) {agg}_{column}' for column in columns for agg in ['sum','min','max']]
            select = ','.join(expressions)
            cursor = con.execute(f"SELECT {select} FROM read_parquet('{GRAPH / (name + '.parquet')}')")
            source = dict(zip([item[0] for item in cursor.description], cursor.fetchone()))
            target_expressions = ['count(*) n']
            for column in columns:
                for aggregate in ['sum', 'min', 'max']:
                    key = f'{aggregate}_{column}'
                    expression = f'{aggregate}({column})'
                    if isinstance(source[key], float):
                        expression = f'toFloat64({expression})'
                    target_expressions.append(f'{expression} {key}')
            target = client.rows(f'SELECT {",".join(target_expressions)} FROM plexus_refresh_graph.{name}')[0]
            for key, expected in source.items():
                actual = float(target[key]) if isinstance(expected, float) else int(target[key])
                equal = math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-8) if isinstance(expected, float) else actual == expected
                assert equal, (name,key,expected,actual)
            checks = client.rows(f'CHECK TABLE plexus_refresh_graph.{name}')
            assert all(row['result'] == 1 for row in checks)
            result.append(dict(table=name,source=source,target=target,checksum_ok=True))
            print(name, 'all numeric aggregates and storage checks match', flush=True)
    (ROOT / 'work/road-coverage/graph-storage-validation.json').write_text(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
