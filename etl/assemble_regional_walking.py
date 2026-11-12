import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from analytics.client import ClickHouse
from import_national_inventory import insert_batch
from normative_walking.regional_assembly import assemble

ROOT = Path(__file__).resolve().parents[1]


def import_network(folder: Path, metadata: dict, region: dict, boundary_hash: str) -> None:
    client = ClickHouse()
    for name in ('normative-walking.sql', 'normative-pedestrian-regions.sql'):
        for sql in (ROOT / 'infra/clickhouse' / name).read_text().split(';'):
            if sql.strip():
                client.request(sql)
    revision = metadata['revision']
    exists = client.rows(f"SELECT revision FROM plexus_normative.pedestrian_networks WHERE revision='{revision}' LIMIT 1")
    if not exists:
        for attempt in range(3):
            try:
                for kind in ('nodes', 'edges', 'origins'):
                    table = 'plexus_normative.pedestrian_' + kind
                    client.request(f"ALTER TABLE {table} DELETE WHERE revision='{revision}' SETTINGS mutations_sync=1")
                    path = folder / (kind + '.parquet')
                    with path.open('rb') as stream:
                        client.request(f'INSERT INTO {table} SETTINGS max_threads=1,max_insert_threads=1,input_format_parallel_parsing=0 FORMAT Parquet', stream, path.stat().st_size)
                for kind, expected in [('nodes', metadata['node_count']), ('edges', metadata['edge_count']), ('origins', metadata['origin_count'])]:
                    count = int(client.rows(f"SELECT count() AS n FROM plexus_normative.pedestrian_{kind} WHERE revision='{revision}'")[0]['n'])
                    if count != expected:
                        raise ValueError('Imported regional walking count differs from its manifest')
                insert_batch(client, 'plexus_normative.pedestrian_networks', [json.dumps(metadata)])
                break
            except RuntimeError as error:
                if 'MEMORY_LIMIT_EXCEEDED' not in str(error) or attempt == 2:
                    raise
                time.sleep(5)
    bound = client.rows(f"SELECT revision FROM plexus_normative.pedestrian_regions WHERE region_id='{region['id']}' AND revision='{revision}' AND purpose='physical' LIMIT 1")
    if not bound:
        binding = {'region_id': region['id'], 'region_name': region['name'], 'purpose': 'physical',
                   'revision': revision, 'published_at': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S.%f'), 'boundary_sha256': boundary_hash}
        insert_batch(client, 'plexus_normative.pedestrian_regions', [json.dumps(binding, ensure_ascii=False)])
    print('regional walking network imported', region['id'], revision, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--region-id', required=True)
    parser.add_argument('--import-storage', action='store_true')
    args = parser.parse_args()
    source_root = ROOT / '.local/normative-national-inputs'
    boundaries = (source_root / 'regions.json').read_bytes()
    region = next(row for row in json.loads(boundaries)['regions'] if row['id'] == args.region_id)
    boundary_hash = hashlib.sha256(boundaries).hexdigest()
    sources = json.loads((source_root / 'osm/manifest.json').read_text())
    raw_root = ROOT / '.local/normative-regional-walking/raw'
    completed = {path.parent.name: json.loads(path.read_text()) for path in raw_root.glob('*/complete.json')}
    if set(completed) != {row['id'] for row in sources}:
        raise ValueError('All acquired walking extracts must complete before regional publication')
    selected = [row for row in sources if args.region_id in completed[row['id']]['regions']]
    if not selected:
        raise ValueError('No raw walking objects for the selected region')
    for source in selected:
        if completed[source['id']]['source']['sha256'] != source['sha256'] or completed[source['id']]['boundary_sha256'] != boundary_hash:
            raise ValueError('Walking source or boundary version mismatch')
    descriptor = json.dumps({'region_id': args.region_id, 'sources': selected, 'boundary_sha256': boundary_hash, 'rules_version': 'pedestrian-regional-v1'}, sort_keys=True)
    digest = hashlib.sha256(descriptor.encode()).hexdigest()
    revision = digest[:24]
    folder = ROOT / '.local/normative-regional-walking/networks' / args.region_id / revision
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / 'manifest.json'
    if manifest.exists():
        evidence = json.loads(manifest.read_text())
    else:
        paths = [raw_root / row['id'] / args.region_id for row in selected]
        counts = assemble(paths, folder, revision)
        timestamps = [next(line.split('=', 1)[1].replace('\\:', ':') for line in row['state'].splitlines() if line.startswith('timestamp=')) for row in selected]
        metadata = {'revision': revision, 'created_at': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'source_url': 'https://download.openstreetmap.fr/extracts/', 'source_sha256': digest,
                    'source_timestamp': min(timestamps), 'rules_version': 'pedestrian-regional-v1',
                    'node_count': counts['nodes'], 'edge_count': counts['edges'], 'origin_count': counts['residential_buildings'],
                    'excluded_counts': {key: value for key, value in counts.items() if key.startswith('conflicting_')}}
        evidence = {'metadata': metadata, 'region': {'id': region['id'], 'name': region['name']}, 'sources': selected,
                    'boundary_sha256': boundary_hash, 'counts': counts,
                    'extent': 'Complete ways intersecting the project boundary; paths outside that clip may be incomplete',
                    'population_and_entrances_verified': False}
        temporary = manifest.with_suffix('.json.part')
        temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(manifest)
    print('regional walking assembled', args.region_id, evidence['counts'], flush=True)
    if args.import_storage:
        import_network(folder, evidence['metadata'], region, boundary_hash)


if __name__ == '__main__':
    main()
