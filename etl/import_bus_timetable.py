import argparse
import json
from hashlib import file_digest
from pathlib import Path

import pyarrow.parquet as pq
from transit_timetable import normalize_timetables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--region-source', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    identifiers = set()
    sources = []
    for path in [args.source, *args.region_source]:
        with path.open('rb') as stream:
            digest = file_digest(stream, 'sha256').hexdigest()
        sources.append({'path': str(path), 'sha256': digest})
    for path in args.region_source:
        identifiers.update(pq.read_table(path, columns=['route_registry_id']).column(0).to_pylist())
    rows = [row for row in pq.read_table(args.source).to_pylist() if row['route_registry_id'] in identifiers]
    result = normalize_timetables(rows)
    result['sources'] = sources
    result['selected_route_ids'] = sorted(identifiers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    print(json.dumps({'trips': len(result['trips']), 'rejected_directions': len(result['rejected']),
                      'source_rows': result['source_rows'], 'source_directions': result['source_directions']}))


if __name__ == '__main__':
    main()
