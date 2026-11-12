import hashlib
import json
import os
import runpy
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for line in (ROOT / '.env.analytics').read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip().strip('\"\'')
sys.path.append(str(ROOT / 'etl'))
from analytics.client import ClickHouse

client = ClickHouse()
seed_tables = ['criteria','facilities','territories','settlement_types','walking_facts','library_facts','medical_facts','fire_facts','fire_destinations','index_bases','inventory_regions','regional_directory_memberships']
existing = client.rows("SELECT name FROM system.tables WHERE database='plexus_normative'")
for row in existing:
    if row['name'] in seed_tables and client.rows('SELECT count() AS n FROM plexus_normative.' + row['name'])[0]['n']:
        raise RuntimeError('Refuse to replace populated normative seed table: ' + row['name'])
files = ['normative.sql','normative-fire.sql','normative-walking.sql','normative-national.sql','normative-regional-snapshots.sql','normative-index-bases.sql','normative-index-map.sql','normative-regional-origins.sql','normative-regional-directories.sql','normative-service-directories.sql','normative-pedestrian-regions.sql','normative-scenario-indices.sql']
for name in files:
    for statement in (ROOT / 'infra/clickhouse' / name).read_text().split(';'):
        if statement.strip():
            if 'plexus_normative' not in statement or any(word in statement.upper() for word in ['DROP ', 'TRUNCATE ', 'DELETE ', 'INSERT ']):
                raise RuntimeError('Unexpected schema statement in ' + name)
            client.request(statement)
    print('schema', name, flush=True)
for name in ['import_normative.py','import_index_bases.py']:
    runpy.run_path(str(ROOT / 'etl' / name), run_name='__main__')
coverage_path = ROOT / 'docs/results/normative-live-index-coverage.json'
coverage = json.loads(coverage_path.read_text())
regions = {}
for criterion in coverage['results']:
    for row in criterion['rows']:
        key, name = row['region_id'], row['region_name']
        if key in regions and regions[key] != name:
            raise RuntimeError('Conflicting archived region name')
        regions[key] = name
if len(regions) != 84:
    raise RuntimeError('Unexpected archived region catalog size')
client.request('INSERT INTO plexus_normative.inventory_regions FORMAT JSONEachRow', '\n'.join(json.dumps({'id': key, 'name': name}, ensure_ascii=False) for key,name in sorted(regions.items())).encode())
runpy.run_path(str(ROOT / 'etl/import_regional_directories.py'), run_name='__main__')
counts = {row['name']:client.rows('SELECT count() AS n FROM plexus_normative.'+row['name'])[0]['n'] for row in client.rows("SELECT name FROM system.tables WHERE database='plexus_normative' ORDER BY name")}
report = {'checked_at':datetime.now(UTC).isoformat(),'scope':'repository normative schema and seed catalogs only; no computed measurement/index restoration or routing','counts':counts,'region_catalog_source':str(coverage_path.relative_to(ROOT)),'region_catalog_sha256':hashlib.sha256(coverage_path.read_bytes()).hexdigest(),'schema_files':files}
Path(__file__).with_name("validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
