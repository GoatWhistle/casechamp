import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl/analytics'))
from client import ClickHouse

DEST = ROOT / 'data/road-refresh'


def main():
    validation = json.loads((DEST / 'staging-validation.json').read_text())
    comparison = json.loads((ROOT / 'work/road-coverage/comparison.json').read_text())
    assert validation['regions_checked'] == comparison['regions_checked'] == 82
    assert json.loads((DEST / 'staged-derived.json').read_text()) == {'roads': True, 'runtime': True, 'corridors': True}
    marker = DEST / 'publication.json'
    if marker.exists():
        raise SystemExit('Publication journal already exists; inspect before repeating')
    for port in [8001, 8003]:
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', port)) == 0:
                raise SystemExit(f'Stop API on port {port} before changing snapshot')
    client = ClickHouse()
    revision = client.rows("SELECT value FROM plexus_refresh_atlas.atlas_metadata WHERE key='graph_revision'")[0]['value']
    assert revision == validation['revision']
    tables = []
    for database in ['casechamp', 'graph', 'atlas']:
        rows = client.rows(f"SELECT name FROM system.tables WHERE database='plexus_refresh_{database}' AND engine='MergeTree' ORDER BY name")
        for row in rows:
            name = row['name']
            assert not name.endswith('__loading')
            tables.append((database, name))
    tables.sort(key=lambda pair: pair == ('atlas', 'atlas_metadata'))
    journal = dict(started_at=datetime.now(timezone.utc).isoformat(), graph_version=validation['version'], completed=[], status='publishing')
    marker.write_text(json.dumps(journal, indent=2))
    try:
        for database, name in tables:
            active, staged = f'plexus_{database}.{name}', f'plexus_refresh_{database}.{name}'
            exists = bool(client.rows(f'EXISTS TABLE {active}')[0]['result'])
            if exists:
                client.request(f'EXCHANGE TABLES {active} AND {staged}')
            else:
                client.request(f'RENAME TABLE {staged} TO {active}')
            journal['completed'].append(dict(database=database, name=name, exchanged=exists))
            marker.write_text(json.dumps(journal, indent=2))
            print(active, flush=True)
    except Exception:
        for item in reversed(journal['completed']):
            active = f"plexus_{item['database']}.{item['name']}"
            staged = f"plexus_refresh_{item['database']}.{item['name']}"
            if item['exchanged']:
                client.request(f'EXCHANGE TABLES {active} AND {staged}')
            else:
                client.request(f'RENAME TABLE {active} TO {staged}')
        journal['status'] = 'rolled_back'
        marker.write_text(json.dumps(journal, indent=2))
        raise
    journal['status'] = 'published_requires_api_smoke'
    journal['published_at'] = datetime.now(timezone.utc).isoformat()
    marker.write_text(json.dumps(journal, indent=2))
    print('Snapshot exchanged; previous tables retained in refresh databases', flush=True)


if __name__ == '__main__':
    main()
