import hashlib
import json
import os
import sys
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'data/road-refresh'
os.environ['OSM_SOURCE'] = str(DEST / 'ways')
sys.path.insert(0, str(ROOT / 'etl'))
import indices
from artifacts import file_record


def main():
    graph = DEST / 'graph/manifest.json'
    assert graph.exists()
    sources = sorted((DEST / 'ways').glob('*.parquet'))
    assert len(sources) == 10
    records = []
    for path in sources:
        record = file_record(path)
        expected = json.loads((DEST / 'sources' / (path.stem + '.json')).read_text())['output']
        assert record == expected
        records.append(record)
    with duckdb.connect(str(DEST / 'input.duckdb'), read_only=True) as con:
        points = con.sql("SELECT oktmo point_id,latitude lat,longitude lon FROM stg_settlements WHERE object_level='Населенный пункт' AND latitude IS NOT NULL AND region NOT IN ('Москва','Санкт-Петербург','Севастополь') ORDER BY oktmo").df()
    assert len(points) == 155412 and points.point_id.is_unique
    points['km_allseason_road'] = indices.rai(points)
    path = DEST / 'rai.parquet'
    pq.write_table(pa.Table.from_pandas(points, preserve_index=False), path, compression='zstd')
    manifest = dict(output=file_record(path), sources=records, graph_manifest_sha256=hashlib.sha256(graph.read_bytes()).hexdigest(), implementation=file_record(ROOT / 'etl/indices.py'))
    (DEST / 'rai-manifest.json').write_text(json.dumps(manifest, indent=2))
    print('RAI distances saved; all ten source Parquets retained', flush=True)


if __name__ == '__main__':
    main()
