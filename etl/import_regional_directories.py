import json
import os
import time
from pathlib import Path

from analytics.client import ClickHouse
from app.domain.normative.model import Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.normative.regional_catalog import CATEGORIES
from import_national_inventory import insert_batch

ROOT = Path(__file__).resolve().parents[1]


def directory_memberships(registrations: list[dict], facilities: list[Facility], regions: set[str]) -> list[dict]:
    by_id = {(f.id, f.service): f for f in facilities}
    result = []
    seen = set()
    for registration in registrations:
        region = registration['region_id']
        category = registration['category']
        service = registration['service']
        if region not in regions or category not in CATEGORIES.values():
            raise ValueError('Directory membership requires a known region and category')
        ids = registration['facility_ids']
        if not isinstance(ids, list) or not ids:
            raise ValueError('Directory membership requires explicit facility identifiers')
        for identifier in ids:
            key = (region, category, service, identifier)
            if key in seen:
                raise ValueError('Duplicate regional directory membership')
            seen.add(key)
            facility = by_id.get((identifier, service))
            if facility is None:
                raise ValueError('Regional directory facility is absent from the imported catalog')
            if facility.source_url != registration['scope_source_url'] or facility.source_sha256 != registration['scope_source_sha256'] or facility.source_sha256 is None:
                raise ValueError('Regional directory scope must match the imported primary source')
            result.append({
                'region_id': region,
                'category': category,
                'facility_id': identifier,
                'service': service,
                'scope_source_url': registration['scope_source_url'],
                'scope_source_sha256': registration['scope_source_sha256'],
            })
    return result


def main() -> None:
    reader = ClickHouseReader(os.environ.get('CLICKHOUSE_URL', 'http://127.0.0.1:18123'), os.environ.get('CLICKHOUSE_USER', 'plexus'), os.environ['CLICKHOUSE_PASSWORD'], max_threads=1)
    registrations = json.loads((ROOT / 'datasets/normative-regional-directories.json').read_text())
    services = sorted({r['service'] for r in registrations})
    facilities = [Facility(**r) for r in reader.rows('SELECT id,service,name,address,source_url,observed_at,latitude,longitude,coordinate_source,coordinate_status,published_on,source_sha256,coordinate_snapshot_sha256,coordinate_snapshot_url FROM plexus_normative.facilities WHERE service IN {services:Array(String)}', {'services': services})]
    regions = {r['id'] for r in reader.rows('SELECT id FROM plexus_normative.inventory_regions FINAL', {})}
    rows = directory_memberships(registrations, facilities, regions)
    client = ClickHouse()
    for statement in (ROOT / 'infra/clickhouse/normative-regional-directories.sql').read_text().split(';'):
        if statement.strip():
            client.request(statement)
    version = time.time_ns()
    insert_batch(client, 'plexus_normative.regional_directory_memberships', [json.dumps({**row, 'version': version}) for row in rows])
    print('Regional directory memberships imported', len(rows))


if __name__ == '__main__':
    main()
