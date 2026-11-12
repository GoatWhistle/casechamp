import argparse
import json
import time
from datetime import UTC, datetime
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def receipt(api: str, region: str, criterion: str) -> dict:
    for attempt in range(4):
        try:
            with urlopen(f'{api}/normative/regions/{region}/measurements/{criterion}/receipt', timeout=90) as response:
                return json.load(response)
        except (OSError, HTTPError, HTTPException, json.JSONDecodeError) as error:
            if attempt == 3:
                raise RuntimeError(f'Walking receipt unavailable: {region}/{criterion}') from error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError('Walking receipt attempts exhausted')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', default='http://127.0.0.1:8003/api/v1')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    expected = {r['id'] for r in json.loads((ROOT / '.local/normative-national-inputs/regions.json').read_text())['regions']}
    networks = {}
    for path in (ROOT / '.local/normative-regional-walking/networks').glob('*/*/manifest.json'):
        metadata = json.loads(path.read_text())['metadata']
        region = path.parent.parent.name
        if region not in networks or metadata['created_at'] > networks[region]['created_at']:
            networks[region] = metadata
    if set(networks) != expected:
        raise ValueError('Walking network manifests do not cover the project territory set')
    checkpoint = ROOT / '.local/regional-walking-receipts-verified.json'
    rows = json.loads(checkpoint.read_text()) if args.resume and checkpoint.exists() else []
    complete = {(r['region_id'], r['criterion_id'], r['graph_revision']) for r in rows}
    for region, metadata in sorted(networks.items()):
        for criterion in ('N04', 'N09'):
            if (region, criterion, metadata['revision']) in complete:
                continue
            result = receipt(args.api, region, criterion)
            if not result or result['mode'] != 'walk' or result['unit'] != 'metres' or result['qualification'] != 'physical_only':
                raise ValueError(f'Unexpected walking receipt model: {region}/{criterion}')
            if result['origins'] != metadata['origin_count'] or result['graph_revision'] != metadata['revision']:
                raise ValueError(f'Walking reference count or revision differs: {region}/{criterion}')
            if result['closed_way_ids'] or not 0 < result['measured_paths'] <= result['origins'] or result['facilities'] <= 0:
                raise ValueError(f'Unexpected walking baseline result: {region}/{criterion}')
            rows.append({key: result[key] for key in ('region_id', 'criterion_id', 'run_id', 'origins', 'measured_paths', 'facilities', 'graph_revision')})
            checkpoint.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
            print('verified walking receipt', region, criterion, result['origins'], flush=True)
    selected = {(r['region_id'], r['criterion_id']): r for r in rows if r['graph_revision'] == networks[r['region_id']]['revision']}
    if len(selected) != 2 * len(expected):
        raise ValueError('Walking receipt verification is incomplete')
    results = list(selected.values())
    evidence = {'checked_at': datetime.now(UTC).isoformat(), 'territories': len(expected), 'calculations': len(results),
                'reference_count_per_criterion': {criterion: sum(r['origins'] for r in results if r['criterion_id'] == criterion) for criterion in ('N04', 'N09')},
                'legal_compliance_confirmed': False,
                'scope': 'All latest saved receipts checked against every imported regional network manifest; not a complete per-route replay or legal qualification', 'results': results}
    (ROOT / 'docs/results/normative-national-walking-measurement-validation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print('national walking receipt validation complete', len(results), flush=True)


if __name__ == '__main__':
    main()
