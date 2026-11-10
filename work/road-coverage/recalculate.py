import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from artifacts import file_record, write_json

DEST = ROOT / 'data/road-refresh'
DB = DEST / 'casechamp.duckdb'
GENERATED = {'np_access', 'np_city_times', 'market_cities', 'market_city_legs',
             'manual_links_ru', 'manual_remote', 'index_model_metadata'}


def initialize() -> None:
    if DB.exists():
        return
    source = str(DEST / 'input.duckdb').replace("'", "''")
    temporary = DB.with_suffix('.loading.duckdb')
    if temporary.exists():
        temporary.unlink()
    with duckdb.connect(str(temporary)) as con:
        con.execute(f"ATTACH '{source}' AS original (READ_ONLY)")
        tables = [row[0] for row in con.execute("SELECT table_name FROM information_schema.tables WHERE table_catalog='original' AND table_schema='main'").fetchall()]
        for table in tables:
            if not re.fullmatch('[a-z0-9_]+', table):
                raise ValueError('Unexpected source table identifier')
            if table in GENERATED or table.startswith('idx_'):
                continue
            con.execute(f'CREATE TABLE {table} AS SELECT * FROM original.{table}')
        con.execute('DETACH original')
    temporary.replace(DB)
    print('Initialized isolated calculation database', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    manifest = DEST / 'graph/manifest.json'
    while not manifest.exists():
        if not args.wait:
            raise SystemExit('Verified candidate graph is not ready')
        print('Awaiting verified candidate graph', flush=True)
        time.sleep(60)
    if shutil.disk_usage(DEST).free < 3_000_000_000:
        raise SystemExit('At least 3 GB free required before candidate calculation')
    initialize()
    state_path = DEST / 'calculation-stages.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        'graph_manifest': file_record(manifest), 'completed': [],
    }
    if state['graph_manifest'] != file_record(manifest):
        raise SystemExit('Graph changed since candidate calculation started')
    environment = dict(os.environ, CASECHAMP_DB=str(DB), GRAPH_INPUT=str(DEST / 'graph'),
                       OSM_SOURCE=str(DEST / 'ways'), ATLAS_INPUT=str(DEST / 'atlas-input.json'),
                       ACCESS_WORKERS='2')
    environment.pop('APPEND_SCENARIOS', None)
    commands = [
        ('manual', ['etl/manual_links.py']),
        *[(f'access-{scenario}', ['work/road-coverage/access_clickhouse.py']) for scenario in
          ['road', 'road_summer', 'road_winter', 'summer', 'winter']],
        ('indices', ['work/road-coverage/indices_cached.py']),
        ('validation', ['etl/validate_indices.py', '--database', str(DB), '--output', str(DEST / 'validation.json')]),
        ('export', ['etl/export_indices.py', '--database', str(DB), '--output', str(DEST / 'indices.json'),
                    '--graph-manifest', str(manifest)]),
    ]
    for stage, command in commands:
        if stage in state['completed']:
            continue
        if stage.startswith('access-'):
            environment['SCENARIOS'] = stage.removeprefix('access-')
            environment['APPEND_SCENARIOS'] = '0' if stage == 'access-road' else '1'
        print(f'Starting {stage}', flush=True)
        with (DEST / f'calculate-{stage}.log').open('w') as output:
            subprocess.run([sys.executable, *command], cwd=ROOT, env=environment,
                           stdout=output, stderr=subprocess.STDOUT, check=True)
        state['completed'].append(stage)
        write_json(state_path, state)
        print(f'Completed {stage}', flush=True)
    print('Candidate indices validated; publication still requires graph and regional comparison', flush=True)


if __name__ == '__main__':
    main()
