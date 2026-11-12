import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from analytics.client import ClickHouse
from extract_national_pois import RegionIndex
from federal_city_origins import city_cells
from import_national_inventory import insert_batch

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    client = ClickHouse()
    boundaries = (ROOT / '.local/normative-national-inputs/regions.json').read_bytes()
    boundary_hash = hashlib.sha256(boundaries).hexdigest()
    index = RegionIndex(json.loads(boundaries)['regions'])
    graph_revision = client.rows("SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_revision'")[0]['value']
    raw = client.request('SELECT point_id,settlement,region,population,node,snap_km,lat,lon FROM plexus_graph.locations ORDER BY point_id SETTINGS max_threads=1,max_block_size=8192 FORMAT JSONEachRow')
    source_hash = hashlib.sha256(raw).hexdigest()
    spatial = []
    for line in raw.splitlines():
        row = json.loads(line)
        if row['lat'] is not None and row['lon'] is not None and row['point_id']:
            region_id, _, status = index.locate(row['lat'], row['lon'])
            if status == 'spatial_match':
                spatial.append({'region_id': region_id, 'latitude': row['lat'], 'longitude': row['lon'],
                                'population': row['population'], 'source_region': row['region'] or ''})
    cells, cities, cells_hash = city_cells(client, index, spatial)
    revision = hashlib.sha256((boundary_hash + source_hash + graph_revision + cells_hash).encode()).hexdigest()[:24]
    for statement in (ROOT / 'infra/clickhouse/normative-regional-origins.sql').read_text().split(';'):
        if statement.strip():
            client.request(statement)
    if client.rows(f"SELECT revision FROM plexus_normative.regional_origin_snapshots WHERE revision='{revision}' LIMIT 1"):
        print('Regional origin snapshot already imported', revision)
        return
    counts, regions = Counter(), Counter()
    batch, seen = [], set()
    for line in raw.splitlines():
        row = json.loads(line)
        if row['lat'] is None or row['lon'] is None or not row['point_id']:
            counts['outside'] += 1
            continue
        region_id, _, status = index.locate(row['lat'], row['lon'])
        counts[status] += 1
        if status != 'spatial_match':
            continue
        key = (region_id, row['point_id'])
        if key in seen:
            raise ValueError('Duplicate origin ID in a spatial region')
        seen.add(key)
        record = {'snapshot': revision, 'region_id': region_id, 'id': row['point_id'],
                  'name': row['settlement'] or row['point_id'], 'population': row['population'],
                  'node': row['node'], 'snap_km': row['snap_km'], 'latitude': row['lat'],
                  'longitude': row['lon'], 'source_region': row['region'] or ''}
        regions[region_id] += 1
        batch.append(json.dumps(record, ensure_ascii=False))
        if len(batch) >= 1000:
            insert_batch(client, 'plexus_normative.regional_origin_points', batch)
            batch = []
    for cell in cells:
        key = (cell['region_id'], cell['id'])
        if key in seen:
            raise ValueError('Duplicate origin ID in a spatial region')
        seen.add(key)
        counts['federal_city_cell'] += 1
        regions[cell['region_id']] += 1
        batch.append(json.dumps({'snapshot': revision, **cell}, ensure_ascii=False))
        if len(batch) >= 1000:
            insert_batch(client, 'plexus_normative.regional_origin_points', batch)
            batch = []
    if batch:
        insert_batch(client, 'plexus_normative.regional_origin_points', batch)
    metadata = {'revision': revision, 'created_at': datetime.now(UTC).isoformat(),
                'graph_revision': graph_revision, 'boundary_sha256': boundary_hash, 'source_sha256': source_hash,
                'assigned': counts['spatial_match'], 'outside': counts['outside'], 'ambiguous': counts['ambiguous']}
    insert_batch(client, 'plexus_normative.regional_origin_snapshots', [json.dumps(metadata)])
    evidence = {**metadata, 'regions': dict(regions), 'federal_city_cells': counts['federal_city_cell'], 'federal_cities': cities,
                'method': 'Unique spatial intersection of existing graph origins with project map polygons; no nearest-region fallback. '
                          'Federal cities that are project territories add 1 km cells: source city population minus settlements already present, '
                          'split by residential building count outside 1 km of those settlements; this is a modelled distribution, not observed cell population'}
    (ROOT / 'docs/results/normative-regional-origin-validation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(evidence), flush=True)


if __name__ == '__main__':
    main()
