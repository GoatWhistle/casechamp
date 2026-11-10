import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from artifacts import file_record, revision, write_json
from download_osm import EXTRACTS

DEST = ROOT / 'data/road-refresh'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    expected = {name.replace('-fed-district', '') for name in EXTRACTS}
    while True:
        found = {path.stem for path in (DEST / 'sources').glob('*.json')}
        missing = sorted(expected - found)
        if not missing:
            break
        print(f'Awaiting verified sources: {", ".join(missing)}', flush=True)
        if not args.wait:
            raise SystemExit(1)
        time.sleep(60)
    records = []
    for name in sorted(expected):
        record = json.loads((DEST / 'sources' / f'{name}.json').read_text())
        source = DEST / 'ways' / f'{name}.parquet'
        if record['output'] != file_record(source):
            raise ValueError(f'{name}: extracted file hash mismatch')
        extraction = json.loads(source.with_suffix('.json').read_text())
        if extraction['extractor'] != file_record(ROOT / 'etl/osm_extract.py'):
            raise ValueError(f'{name}: extractor revision mismatch')
        for dependency, signature in extraction['policy'].items():
            if signature != file_record(ROOT / 'etl' / dependency):
                raise ValueError(f'{name}: policy mismatch')
        records.append(record)
    actual = {path.stem for path in (DEST / 'ways').glob('*.parquet')}
    if actual != expected:
        raise ValueError('Candidate input file set differs from ten verified extracts')
    output = DEST / 'graph'
    environment = dict(os.environ, OSM_SOURCE=str(DEST / 'ways'), GRAPH_OUTPUT=str(output),
                       CASECHAMP_DB=str(DEST / 'input.duckdb'))
    environment.pop('OSM_GLOB', None)
    environment.pop('POINT_REGION', None)
    subprocess.run([sys.executable, str(ROOT / 'etl/graph_russia.py')], env=environment, check=True)
    subprocess.run([sys.executable, str(ROOT / 'work/road-coverage/validate_graph.py')], check=True)
    files = [output / f'{name}.parquet' for name in ['nodes', 'edges', 'points', 'ways']]
    manifest = {'code': revision(), 'sources': records,
                'outputs': [file_record(path) for path in files],
                'rows': {path.stem: pq.read_metadata(path).num_rows for path in files},
                'status': 'candidate_requires_connectivity_and_index_validation'}
    write_json(output / 'manifest.json', manifest)
    print(json.dumps(manifest['rows']), flush=True)


if __name__ == '__main__':
    main()
