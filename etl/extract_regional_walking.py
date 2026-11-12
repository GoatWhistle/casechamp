import argparse
import hashlib
import json
from pathlib import Path

import osmium

from extract_national_pois import RegionIndex
from normative_walking.regional_raw import RegionalRaw

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--district', required=True)
    args = parser.parse_args()
    source_root = ROOT / '.local/normative-national-inputs'
    source = next(row for row in json.loads((source_root / 'osm/manifest.json').read_text()) if row['id'] == args.district)
    pbf = source_root / 'osm' / (args.district + '.osm.pbf')
    digest = hashlib.sha256()
    with pbf.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != source['sha256'] or pbf.stat().st_size != source['bytes']:
        raise ValueError('Pedestrian source differs from its acquisition manifest')
    output = ROOT / '.local/normative-regional-walking/raw' / args.district
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'complete.json').exists():
        known = json.loads((output / 'complete.json').read_text())
        if known['source']['sha256'] != source['sha256']:
            raise ValueError('Completed raw extraction belongs to another source')
        print('cached walking raw', args.district, flush=True)
        return
    boundaries = (source_root / 'regions.json').read_bytes()
    extractor = RegionalRaw(output, RegionIndex(json.loads(boundaries)['regions']))
    processor = osmium.FileProcessor(str(pbf)).with_locations().with_filter(osmium.filter.KeyFilter('highway', 'building', 'barrier', 'foot', 'access', 'locked'))
    processed = 0
    print('extracting walking raw', args.district, flush=True)
    for obj in processor:
        extractor.process(obj)
        processed += 1
        if processed % 250000 == 0:
            print('walking objects processed', args.district, processed, flush=True)
    metadata = {'source': source, 'boundary_sha256': hashlib.sha256(boundaries).hexdigest(),
                'rules_version': 'pedestrian-regional-v1', **extractor.finish()}
    temporary = output / 'complete.json.part'
    temporary.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(output / 'complete.json')
    print('walking raw completed', args.district, json.dumps(metadata['regions']), flush=True)


if __name__ == '__main__':
    main()
