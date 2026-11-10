import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from artifacts import file_record, write_json
from download_osm import EXTRACTS

DEST = ROOT / 'data/road-refresh'
LOCK = threading.Lock()


def curl(url: str, destination: Path, resume: bool = False) -> None:
    for attempt in range(5):
        result = subprocess.run([
            'curl', '-fsSL', '--retry', '2', '--retry-delay', '3',
            '--connect-timeout', '30', '--max-time', '2400',
            *(['--continue-at', '-'] if resume else []),
            '-o', str(destination), url,
        ])
        if result.returncode == 0:
            return
        if result.returncode not in {6, 7, 18, 28, 35, 52, 56} or attempt == 4:
            result.check_returncode()
        time.sleep(5 * (attempt + 1))


def collect(name: str, date: str) -> dict:
    short = name.replace('-fed-district', '')
    raw = DEST / 'raw' / f'{short}.osm.pbf'
    output = DEST / 'ways' / f'{short}.parquet'
    manifest = DEST / 'sources' / f'{short}.json'
    if manifest.exists() and output.exists():
        record = json.loads(manifest.read_text())
        if record['output'] == file_record(output):
            print(f'{short}: verified existing collection', flush=True)
            return record
    url = f'https://download.geofabrik.de/russia/{name}-{date}.osm.pbf'
    checksum_path = raw.with_suffix('.md5')
    curl(url + '.md5', checksum_path)
    expected = checksum_path.read_text().split()[0].lower()
    if not raw.exists():
        if shutil.disk_usage(DEST).free < 1_400_000_000:
            raise RuntimeError('Less than 1.4 GB free before download')
        temporary = raw.with_suffix('.part')
        print(f'{short}: downloading {url}', flush=True)
        curl(url, temporary, resume=True)
        temporary.replace(raw)
    digest = hashlib.md5()
    with raw.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError(f'{short}: source MD5 mismatch')
    source = file_record(raw)
    with LOCK:
        print(f'{short}: verified download, extracting', flush=True)
        environment = dict(os.environ, OSM_OUTPUT=str(DEST / 'ways'))
        with (DEST / f'{short}.log').open('w') as log:
            subprocess.run([sys.executable, str(ROOT / 'etl/osm_extract.py'), str(raw)],
                           env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
        extracted = json.loads(output.with_suffix('.json').read_text())
        record = {
            'source_url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'license': 'ODbL-1.0', 'source': source, 'source_md5': expected,
            'output': file_record(output), 'ways': extracted['ways'],
            'service_ways': extracted['service_ways'],
            'invalid_location_ways': extracted['invalid_location_ways'],
            'raw_retained': False,
        }
        write_json(manifest, record)
        raw.unlink()
        print(f'{short}: complete {record["ways"]} ways, {record["service_ways"]} service', flush=True)
        return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default='261109')
    parser.add_argument('--exclude', nargs='*', default=[])
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    for directory in ['raw', 'ways', 'sources']:
        (DEST / directory).mkdir(parents=True, exist_ok=True)
    selected = [name for name in EXTRACTS if name not in args.exclude and (not args.only or name in args.only)]
    selected.sort(key=lambda name: -(DEST / 'raw' / f'{name.replace("-fed-district", "")}.osm.part').stat().st_size
                  if (DEST / 'raw' / f'{name.replace("-fed-district", "")}.osm.part').exists() else 0)
    records, failures = [], {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(collect, name, args.date): name for name in selected}
        for future in as_completed(futures):
            name = futures[future]
            try:
                records.append(future.result())
            except Exception as error:
                failures[name] = str(error)
                print(f'{name}: FAILED {error}', flush=True)
            write_json(DEST / 'progress.json', {'completed': records, 'failed': failures})
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
