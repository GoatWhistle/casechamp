import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import duckdb
import pyarrow as pa
from pyarrow import ipc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl/analytics'))
from catalog import identifier, table_ddl
from client import ClickHouse
from import_data import verify_nulls

DEST = ROOT / 'data/road-refresh'
PREFIX = 'plexus_refresh_'


def stream(client, connection, target, query):
    count = 0
    for batch in connection.execute(query).fetch_record_batch(250000):
        if shutil.disk_usage(ROOT).free < 1_000_000_000:
            raise RuntimeError('Less than 1 GB free on the host; staging paused before insertion')
        buffer = pa.BufferOutputStream()
        with ipc.new_stream(buffer, batch.schema) as writer:
            writer.write_batch(batch)
        client.request(f'INSERT INTO {target} FORMAT ArrowStream', buffer.getvalue().to_pybytes())
        count += batch.num_rows
    actual = int(client.rows(f'SELECT count() n FROM {target}')[0]['n'])
    if actual != count:
        raise ValueError(f'{target}: {actual} != {count}')
    return count


def stage(client, connection, database, name, query):
    target = PREFIX + database + '.' + identifier(name)
    loading = PREFIX + database + '.' + identifier(name + '__loading')
    columns = connection.execute('DESCRIBE ' + query).fetchall()
    fields = ','.join(
        f'CAST({identifier(row[0])} AS VARCHAR) AS {identifier(row[0])}' if row[1] == 'DATE'
        else f'to_json({identifier(row[0])}) AS {identifier(row[0])}' if row[1].endswith('[]')
        else identifier(row[0]) for row in columns
    )
    client.request(f'DROP TABLE IF EXISTS {loading}')
    client.request(table_ddl(loading, name, columns))
    count = stream(client, connection, loading, f'SELECT {fields} FROM ({query})')
    verify_nulls(client, connection, query, loading, columns)
    if client.rows(f'EXISTS TABLE {target}')[0]['result']:
        client.request(f'EXCHANGE TABLES {target} AND {loading}')
        client.request(f'DROP TABLE {loading}')
    else:
        client.request(f'RENAME TABLE {loading} TO {target}')
    print(f'{target}: {count} rows', flush=True)
    return count


def metadata(client, con):
    manifest = json.loads((DEST / 'index-manifest.json').read_text())
    graph_hash = hashlib.sha256((DEST / 'graph/manifest.json').read_bytes()).hexdigest()
    revision = json.dumps([manifest['model_version'], graph_hash, manifest['artifact_version']])
    values = {row['key']: row['value'] for row in client.rows('SELECT key,value FROM plexus_atlas.atlas_metadata')}
    values.update(model_version=manifest['model_version'], graph_revision=revision,
                  graph_version='road-' + hashlib.sha256(revision.encode()).hexdigest()[:16],
                  artifact_version=manifest['artifact_version'])
    rows = pa.Table.from_pylist([{'key': k, 'value': v} for k, v in values.items()])
    con.register('metadata_rows', rows)
    stage(client, con, 'atlas', 'atlas_metadata', 'SELECT * FROM metadata_rows')
    return values


def atlas_indices(client, con):
    rows = json.loads((DEST / 'indices.json').read_text())
    converted = []
    for index, row in enumerate(rows):
        converted.append(dict(region_id=row['region_id'], scenario=row['season'],
            hansen=row['hansen_idx'], covered_population=int(row['covered_population']),
            total_population=int(row['population']), covered_settlements=int(row['covered_settlements']),
            total_settlements=int(row['n_np']), model_version=row['model_version'],
            artifact_version=row['artifact_version'], hansen_1h=row['hansen_1h'],
            hansen_2h=row['hansen_2h'], hansen_4h=row['hansen_4h'], ordinal=index))
    con.register('index_rows', pa.Table.from_pylist(converted))
    for name in ['atlas_indices', 'atlas_exported_indices']:
        stage(client, con, 'atlas', name, 'SELECT * FROM index_rows')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('part', choices=['graph', 'calculation'])
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    ready = DEST / ('graph/manifest.json' if args.part == 'graph' else 'index-manifest.json')
    while not ready.exists():
        if not args.wait:
            raise SystemExit(f'Missing {ready}')
        time.sleep(30)
    fingerprint = hashlib.sha256(ready.read_bytes()).hexdigest()
    state_path = DEST / f'staged-{args.part}.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'fingerprint': fingerprint, 'tables': {}}
    if fingerprint != state['fingerprint']:
        raise ValueError('Candidate changed after staging started')
    client = ClickHouse()
    for database in ['graph', 'casechamp', 'atlas']:
        client.request('CREATE DATABASE IF NOT EXISTS ' + PREFIX + database)
    with duckdb.connect(str(DEST / 'casechamp.duckdb') if args.part == 'calculation' else ':memory:', read_only=args.part == 'calculation') as con:
        if args.part == 'graph':
            queries = {name: "SELECT * FROM read_parquet('" + str(DEST / 'graph' / (name + '.parquet')) + "')" for name in ['nodes', 'edges', 'points', 'ways']}
            database = 'graph'
        else:
            queries = {row[0]: 'SELECT * FROM ' + identifier(row[0]) for row in con.execute('SHOW TABLES').fetchall() if not row[0].startswith('stg_')}
            database = 'casechamp'
        for name, query in queries.items():
            if name not in state['tables']:
                state['tables'][name] = stage(client, con, database, name, query)
                state_path.write_text(json.dumps(state, indent=2))
        if args.part == 'calculation':
            for name in ['stg_settlements', 'stg_intercity']:
                client.request(f'CREATE VIEW IF NOT EXISTS {PREFIX}casechamp.{name} AS SELECT * FROM plexus_casechamp.{name}')
            atlas_indices(client, con)
            state['metadata'] = metadata(client, con)
        state['complete'] = True
        state_path.write_text(json.dumps(state, indent=2))
    print(f'{args.part}: staging complete', flush=True)


if __name__ == '__main__':
    main()
