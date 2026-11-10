import csv
import json
from collections import Counter
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
atlas = json.loads((ROOT / 'frontend/atlas/public/atlas.json').read_text())
regions = sorted(atlas['regions'], key=lambda row: row['name'])
prefixes = {
    row['id'][:3] if row['id'][2] != '0' else row['id'][:2]: row['id']
    for row in regions
}
connection = duckdb.connect(str(ROOT / 'data/casechamp.duckdb'), read_only=True)
counts = Counter()
outside = Counter()
for oktmo, mode, count in connection.execute('''
    select oktmo_from, transport_type, count(*) from stg_intercity
    where distance_hr is not null group by 1, 2
''').fetchall():
    region_id = prefixes.get(oktmo[:3], prefixes.get(oktmo[:2]))
    if region_id:
        counts[region_id, mode] += count
    else:
        outside[oktmo[:2], mode] += count
rows = []
for region in regions:
    local = Counter(link['mode'] for link in atlas['links'] if link['region'] == region['id'])
    rows.append({
        'id': region['id'], 'name': region['name'],
        'atlas_rail_links': local['rail'], 'atlas_air_links': local['air'],
        'model_rail_outgoing_pairs': counts[region['id'], 'rail'],
        'model_air_outgoing_pairs': counts[region['id'], 'air'],
    })
(OUT / 'local-coverage.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
with (OUT / 'local-coverage.csv').open('w') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
for key in ('atlas_rail_links', 'atlas_air_links', 'model_rail_outgoing_pairs', 'model_air_outgoing_pairs'):
    missing = [row['name'] for row in rows if row[key] == 0]
    print(key, 'missing:', len(missing), '; '.join(missing))
print('Outside atlas:', dict(outside))
assert len(rows) == 82 and len({row['id'] for row in rows}) == 82
