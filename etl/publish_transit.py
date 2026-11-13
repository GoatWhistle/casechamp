import argparse
import json
from datetime import UTC, date, datetime
from hashlib import sha256
from math import isfinite
from pathlib import Path
from uuid import uuid4

from analytics.client import ClickHouse

DDL = {
    'snapshots': 'id String,published_at String,source_date String,source_url String,input_sha256 String,stop_count UInt32,connection_count UInt32,metadata String',
    'stops': 'snapshot String,id String,name String,region_id String,region_code String,latitude Nullable(Float64),longitude Nullable(Float64),coordinate_status String,coordinate_source_url String,coordinate_source_sha256 String',
    'connections': 'snapshot String,trip_id String,source String,target String,departure UInt32,arrival UInt32,sequence UInt32,source_file String,source_sheet String,source_row UInt32,target_row UInt32',
}
KEYS = {'snapshots': 'id', 'stops': '(snapshot,id)', 'connections': '(snapshot,trip_id,sequence)'}


def build_rows(timetable: dict, pins: list[dict], regions: list[dict], snapshot: str) -> tuple[list[dict], list[dict]]:
    mapped = {row['stop_region_code']: row['atlas_region_id'] for row in regions}
    coordinates = {}
    for pin in pins:
        if pin['coordinate_status'] != 'official_operator_pin':
            continue
        if not (isfinite(pin['latitude']) and -90 <= pin['latitude'] <= 90
                and isfinite(pin['longitude']) and -180 <= pin['longitude'] <= 180):
            raise ValueError('Invalid verified stop coordinates')
        identifier = pin['stop_registry_id']
        previous = coordinates.get(identifier)
        if previous and (previous['latitude'], previous['longitude']) != (pin['latitude'], pin['longitude']):
            raise ValueError('Conflicting verified stop coordinates')
        coordinates[identifier] = pin
    stops, connections = {}, []
    for trip in timetable['trips']:
        if trip['calendar'] != 'daily_all_year':
            raise ValueError('Unsupported timetable calendar')
        for stop in trip['stops']:
            identifier = stop['stop_id']
            region = stop['region_code']
            if identifier in stops and stops[identifier]['region_code'] != region:
                raise ValueError('Conflicting stop region codes')
            pin = coordinates.get(identifier, {})
            stops.setdefault(identifier, {
                'snapshot': snapshot, 'id': identifier, 'name': stop['name'],
                'region_id': mapped.get(region) or '', 'region_code': region,
                'latitude': pin.get('latitude'), 'longitude': pin.get('longitude'),
                'coordinate_status': pin.get('coordinate_status', 'unresolved'),
                'coordinate_source_url': pin.get('source_url', ''),
                'coordinate_source_sha256': pin.get('source_sha256', ''),
            })
        for sequence, (start, end) in enumerate(zip(trip['stops'], trip['stops'][1:])):
            departure, arrival = start['departure_seconds'], end['arrival_seconds']
            if departure is None or arrival is None or not 0 <= departure <= arrival < 86400:
                raise ValueError('Connection requires ordered same-day source clocks')
            connections.append({'snapshot': snapshot, 'trip_id': trip['id'], 'source': start['stop_id'],
                                'target': end['stop_id'], 'departure': departure, 'arrival': arrival,
                                'sequence': sequence, 'source_file': trip['source_file'],
                                'source_sheet': trip['source_sheet'], 'source_row': start['source_row'],
                                'target_row': end['source_row']})
    if len({(row['trip_id'], row['sequence']) for row in connections}) != len(connections):
        raise ValueError('Duplicate trip connection identity')
    return sorted(stops.values(), key=lambda row: row['id']), sorted(connections, key=lambda row: (row['trip_id'], row['sequence']))


def insert(client: ClickHouse, table: str, rows: list[dict]) -> None:
    if rows:
        body = '\n'.join(json.dumps(row, ensure_ascii=False, allow_nan=False) for row in rows).encode()
        client.request(f'INSERT INTO plexus_transit.{table} FORMAT JSONEachRow', body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--timetable', type=Path, required=True)
    parser.add_argument('--coordinates', type=Path, action='append', required=True)
    parser.add_argument('--regions', type=Path, required=True)
    parser.add_argument('--source-date', type=date.fromisoformat, required=True)
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    paths = [args.timetable, *args.coordinates, args.regions]
    sources = [{'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest()} for path in paths]
    input_sha = sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    pins = [row for path in args.coordinates for row in json.loads(path.read_text())['coordinates']]
    for path in args.coordinates:
        for pin in json.loads(path.read_text())['coordinates']:
            if pin['coordinate_status'] != 'official_operator_pin':
                continue
            source = path.parent / pin['source_file']
            if source.resolve().parent != path.parent.resolve() or sha256(source.read_bytes()).hexdigest() != pin['source_sha256']:
                raise ValueError('Coordinate source snapshot checksum mismatch')
    snapshot = 'transit-' + uuid4().hex
    timetable = json.loads(args.timetable.read_text())
    stops, connections = build_rows(timetable, pins, json.loads(args.regions.read_text()), snapshot)
    client = ClickHouse()
    client.request('CREATE DATABASE IF NOT EXISTS plexus_transit')
    for table, columns in DDL.items():
        client.request(f'CREATE TABLE IF NOT EXISTS plexus_transit.{table} ({columns}) ENGINE=MergeTree ORDER BY {KEYS[table]}')
    insert(client, 'stops', stops)
    insert(client, 'connections', connections)
    for table, expected, order in [('stops', stops, 'id'), ('connections', connections, 'trip_id,sequence')]:
        actual = client.rows(f"SELECT * FROM plexus_transit.{table} WHERE snapshot='{snapshot}' ORDER BY {order}")
        if actual != expected:
            raise ValueError(f'Transit {table} round-trip mismatch; snapshot remains unpublished')
    record = {'id': snapshot, 'published_at': datetime.now(UTC).isoformat(),
              'source_date': args.source_date.isoformat(), 'source_url': args.source_url, 'input_sha256': input_sha,
              'stop_count': len(stops), 'connection_count': len(connections),
              'metadata': json.dumps({'sources': sources, 'clock_basis': 'source_clock', 'timezone_verified': False,
                                      'operating_service_verified': False, 'coverage_complete': False,
                                      'rejected_directions': len(timetable['rejected'])}, ensure_ascii=False)}
    insert(client, 'snapshots', [record])
    if client.rows(f"SELECT * FROM plexus_transit.snapshots WHERE id='{snapshot}'") != [record]:
        raise ValueError('Published snapshot read-back mismatch')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'snapshot': snapshot, 'stops': len(stops), 'connections': len(connections),
                      'located_stops': sum(row['latitude'] is not None for row in stops)}))


if __name__ == '__main__':
    main()
