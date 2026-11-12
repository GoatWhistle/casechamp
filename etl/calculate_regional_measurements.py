import argparse
import json
import time
from http.client import HTTPException
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CRITERIA = ('N01', 'N02', 'N05', 'N06', 'N07', 'N08')


def request(url: str, method: str = 'GET') -> tuple[int, object]:
    body = b'{"closed_way_ids":[]}' if method == 'POST' else None
    query = Request(url, data=body, method=method, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(query, timeout=600) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read())


def save(path: Path, records: list[dict]) -> None:
    temporary = path.with_suffix('.json.part')
    temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', default='http://127.0.0.1:8003/api/v1')
    parser.add_argument('--regions', type=Path, default=Path('.local/normative-national-inputs/regions.json'))
    parser.add_argument('--output', type=Path, default=Path('.local/regional-measurements-batch.json'))
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--criteria', nargs='+', choices=('N01', 'N02', 'N04', 'N05', 'N06', 'N07', 'N08', 'N09'), default=CRITERIA)
    args = parser.parse_args()
    records = json.loads(args.output.read_text()) if args.resume and args.output.exists() else []
    complete = {(row['region_id'], row['criterion_id']) for row in records if row['status'] == 200}
    regions = json.loads(args.regions.read_text())['regions']
    for region in regions:
        for criterion in args.criteria:
            if (region['id'], criterion) in complete:
                continue
            url = args.api + '/normative/regions/' + region['id'] + '/measurements/' + criterion + '/receipt'
            started = time.perf_counter()
            catalog_url = args.api + '/normative/regions/' + region['id'] + '/catalog/' + criterion
            for catalog_attempt in range(3):
                try:
                    catalog_status, catalog = request(catalog_url)
                except (OSError, URLError, HTTPException, json.JSONDecodeError):
                    catalog_status, catalog = 503, {'code': 'catalog_connection_unavailable'}
                if catalog_status == 200:
                    break
                if catalog_attempt < 2:
                    time.sleep(5)
            if catalog_status != 200:
                record = {'region_id': region['id'], 'region_name': region['name'], 'criterion_id': criterion,
                          'status': catalog_status, 'stage': 'catalog', 'error': catalog,
                          'observed_at': datetime.now(UTC).isoformat()}
                records.append(record)
                save(args.output, records)
                print(json.dumps(record, ensure_ascii=False), flush=True)
                continue
            if catalog['candidate_count'] == 0:
                record = {'region_id': region['id'], 'region_name': region['name'], 'criterion_id': criterion,
                          'status': 204, 'reason': 'no_loaded_candidates', 'observed_at': datetime.now(UTC).isoformat()}
                records.append(record)
                save(args.output, records)
                print(json.dumps(record, ensure_ascii=False), flush=True)
                continue
            try:
                cached_status, cached = request(url) if args.resume else (204, None)
            except (OSError, URLError, HTTPException, json.JSONDecodeError):
                cached_status, cached = 503, None
            reusable = cached_status == 200 and cached and not cached['closed_way_ids']
            for attempt in range(3):
                try:
                    status, body = (200, cached) if reusable else request(url, 'POST')
                except (OSError, URLError, HTTPException, json.JSONDecodeError) as error:
                    if attempt == 2:
                        status, body = 503, {'code': 'regional_response_unavailable', 'error_type': type(error).__name__}
                        break
                    time.sleep(5)
                    continue
                if status >= 500 and attempt < 2:
                    time.sleep(5)
                    continue
                break
            record = {'region_id': region['id'], 'region_name': region['name'], 'criterion_id': criterion,
                      'observed_at': datetime.now(UTC).isoformat(), 'status': status,
                      'elapsed_seconds': time.perf_counter() - started}
            if status == 200:
                record.update(run_id=body['run_id'], origins=body['origins'],
                              measured_paths=body['measured_paths'],
                              mode=body['mode'], unit=body['unit'],
                              facilities=body['facilities'], qualification=body['qualification'], graph_revision=body['graph_revision'])
            else:
                record['error'] = body
            records.append(record)
            save(args.output, records)
            print(json.dumps(record, ensure_ascii=False), flush=True)
    print('Regional measurement batch finished', len(records), flush=True)


if __name__ == '__main__':
    main()
