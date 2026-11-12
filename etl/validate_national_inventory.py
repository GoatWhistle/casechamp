import json
from datetime import UTC, datetime
from pathlib import Path

from analytics.client import ClickHouse


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    client = ClickHouse()
    source_root = root / '.local/normative-national-inputs'
    manifest = json.loads((source_root / 'osm/manifest.json').read_text())
    summaries = [json.loads(p.read_text()) for p in sorted((source_root / 'derived').glob('*.summary.json'))]

    def rows(sql: str) -> list[dict]:
        return [json.loads(line) for line in client.request(sql + ' FORMAT JSONEachRow').decode().splitlines()]

    totals = rows('SELECT count() AS objects,uniqExact(region_id) AS represented_regions FROM plexus_normative.national_inventory FINAL')[0]
    regional = rows('SELECT region_id,any(region_name) AS region_name,category,count() AS objects FROM plexus_normative.national_inventory FINAL ARRAY JOIN categories AS category GROUP BY region_id,category ORDER BY region_id,category')
    regions = rows('SELECT id,name FROM plexus_normative.inventory_regions FINAL ORDER BY id')
    represented = {row['region_id'] for row in regional}
    result = {
        'verified_at': datetime.now(UTC).isoformat(),
        'method': 'Spatial intersection with stored regional polygons; unique OSM object IDs within each region using ClickHouse FINAL',
        'planned_districts': 8,
        'acquired_districts': sum(row['id'].endswith('_federal_district') for row in manifest),
        'extracted_districts': sum(row['district'].endswith('_federal_district') for row in summaries),
        'totals': totals,
        'acquired_extracts': len(manifest),
        'extracted_extracts': len(summaries),
        'sources': manifest,
        'regional_categories': regional,
        'regions_without_loaded_objects': [r for r in regions if r['id'] not in represented],
        'completeness_verified': False,
        'operational_status_verified': False,
        'national_accessibility_calculated': False,
        'limitations': ['OSM objects are not unique institutions', 'Generic medical objects do not establish adult cardiology profiles', 'Some border regions are only partially covered until all extracts are imported', 'Open ways and relations are omitted; missing geometries are counted in extraction summaries'],
    }
    output = root / 'docs/results/normative-national-inventory-validation.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('acquired_districts', 'extracted_districts', 'totals')}))


if __name__ == '__main__':
    main()
