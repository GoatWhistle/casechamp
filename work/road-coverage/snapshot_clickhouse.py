import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pyarrow.ipc as ipc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
sys.path.insert(0, str(ROOT / 'etl/analytics'))
from artifacts import file_record, write_json
from client import ClickHouse

DEST = ROOT / 'data/road-refresh'


def main() -> None:
    client = ClickHouse()
    temporary = DEST / 'input.loading.duckdb'
    destination = DEST / 'input.duckdb'
    if destination.exists():
        raise SystemExit('Input snapshot already exists; preserve it during calculation')
    records = []
    with duckdb.connect(str(temporary)) as con:
        for name in ['stg_settlements', 'stg_intercity']:
            table = ipc.open_stream(io.BytesIO(client.request(f'SELECT * FROM plexus_casechamp.{name} FORMAT ArrowStream'))).read_all()
            expected = int(client.rows(f'SELECT count() AS n FROM plexus_casechamp.{name}')[0]['n'])
            assert table.num_rows == expected
            con.register('source_rows', table)
            con.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM source_rows')
            con.unregister('source_rows')
            records.append({'table': 'plexus_casechamp.' + name, 'rows': expected})
            print(name, expected, flush=True)
    temporary.replace(destination)
    baseline = DEST / 'baseline'
    baseline.mkdir(exist_ok=True)
    points = ipc.open_stream(io.BytesIO(client.request('SELECT * FROM plexus_graph.points ORDER BY point_id FORMAT ArrowStream'))).read_all()
    pq.write_table(points, baseline / 'points.parquet', compression='zstd')
    regions = client.rows('SELECT id,name FROM plexus_atlas.atlas_regions ORDER BY ordinal')
    assert len(regions) == 82
    write_json(DEST / 'atlas-input.json', {'regions': regions})
    indices = client.rows('SELECT * FROM plexus_atlas.atlas_indices ORDER BY scenario,region_id')
    (baseline / 'indices.json').write_text(json.dumps(indices, ensure_ascii=False, indent=2) + '\n')
    write_json(DEST / 'input-manifest.json', {
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'source': 'local ClickHouse', 'tables': records,
        'files': [file_record(destination), file_record(baseline / 'points.parquet'),
                  file_record(DEST / 'atlas-input.json'), file_record(baseline / 'indices.json')],
    })
    print('Isolated input snapshot is ready', flush=True)


if __name__ == '__main__':
    main()
