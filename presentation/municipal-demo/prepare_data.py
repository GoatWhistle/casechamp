import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
features = json.loads((ROOT / 'datasets/municipal-boundaries/municipalities.geojson').read_text())['features']
features = [f for f in features if f['properties']['region_id'] == '07000000']
records = json.loads((ROOT / 'docs/results/south-agent-access-chain.json').read_text())['records']
detail = records[0]['detail']
points = [{'name': p['row']['name'], 'xy': [p['row']['longitude'], p['row']['latitude']], 'minutes': round(p['row']['minutes'], 1)} for p in detail['points']]
facility = detail['points'][0]['facility']
transit = json.loads((ROOT / 'docs/results/transit-api-agent-validation.json').read_text())['api']
result = {'features': [], 'points': points, 'facility': {'name': facility['name'], 'xy': [facility['longitude'], facility['latitude']]}, 'transit': transit['map_target']}
for f in features:
    polygons = f['geometry']['coordinates']
    if f['geometry']['type'] == 'Polygon':
        polygons = [polygons]
    rings = []
    for polygon in polygons:
        for ring in polygon:
            step = max(1, len(ring) // 180)
            sampled = ring[::step]
            if sampled[-1] != ring[-1]:
                sampled.append(ring[-1])
            rings.append([[round(x, 5), round(y, 5)] for x, y, *rest in sampled])
    result['features'].append({'id': f['properties']['id'], 'name': f['properties']['name'], 'rings': rings})
(ROOT / 'presentation/municipal-demo/data.json').write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
print('Prepared', len(features), 'Stavropol municipalities')
