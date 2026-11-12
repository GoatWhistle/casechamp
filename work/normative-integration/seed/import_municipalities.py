import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "datasets/municipal-boundaries/municipalities.geojson"
for line in (ROOT / '.env.analytics').read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=',1)
        os.environ[key.strip()] = value.strip().strip('\"\'')
sys.path.append(str(ROOT / 'etl'))
from analytics.client import ClickHouse

client = ClickHouse()
client.request('''CREATE TABLE IF NOT EXISTS plexus_atlas.municipal_boundaries (id String,region_id String,name String,admin_level UInt8,osm_relation_id Int64,geometry_json String,bounds Tuple(Float64,Float64,Float64,Float64),source_url String,observed_at String,source_sha256 String,region_assignment String,region_overlap_fraction Float64,version UInt64) ENGINE=ReplacingMergeTree(version) ORDER BY(region_id,id)''')
if int(client.rows('SELECT count() AS n FROM plexus_atlas.municipal_boundaries')[0]['n']):
    raise RuntimeError('Refuse to duplicate populated municipal import')
features = json.loads(SOURCE.read_text())['features']
version = time.time_ns()
rows = []
for feature in features:
    props = feature['properties']
    record = {key:props[key] for key in ('id','region_id','name','admin_level','osm_relation_id','bounds','source_url','observed_at','source_sha256','region_assignment','region_overlap_fraction')}
    record['geometry_json'] = json.dumps(feature['geometry'],separators=(',',':'))
    record['version'] = version
    rows.append(json.dumps(record,ensure_ascii=False))
for start in range(0,len(rows),25):
    client.request('INSERT INTO plexus_atlas.municipal_boundaries SETTINGS max_threads=1,max_insert_threads=1,input_format_parallel_parsing=0 FORMAT JSONEachRow','\n'.join(rows[start:start+25]).encode())
counts = client.rows('SELECT region_id,count() AS features FROM plexus_atlas.municipal_boundaries FINAL GROUP BY region_id ORDER BY region_id')
print(json.dumps({'imported':len(features),'regions':counts},ensure_ascii=False,indent=2))
Path('/private/tmp/plexus-geography/data/municipal-boundaries/import-validation.json').write_text(json.dumps({'imported':len(features),'regions':counts},ensure_ascii=False,indent=2))
