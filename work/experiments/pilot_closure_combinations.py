import json
import math
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from urllib.request import Request, urlopen

BASE = 'http://localhost:8081/api/v1/pilots/tuva'
with urlopen(BASE, timeout=5) as response:
    pilot = json.load(response)
points = [point['id'] for point in pilot['points']]
index = {point: i for i, point in enumerate(points)}
editable = [edge['id'] for edge in pilot['edges'] if edge['editable']]
assert len(editable) == 7
scheduled = {'air', 'river', 'scheduled_ferry', 'rail'}
sets = [tuple(group) for count in range(len(editable) + 1) for group in combinations(editable, count)]

def check(case):
    season, disabled = case
    payload = {'season': season, 'model_version': pilot['model_version'],
               'artifact_version': pilot['artifact_version'],
               'changes': [{'edge_id': edge, 'enabled': False} for edge in disabled]}
    request = Request(BASE + '/evaluate', data=json.dumps(payload).encode(),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=10) as response:
        actual = json.load(response)
    d = [[math.inf] * len(points) for _ in points]
    for i in range(len(points)):
        d[i][i] = 0.0
    for edge in pilot['edges']:
        if edge['id'] in disabled or season not in edge['seasons']:
            continue
        frequency = edge['frequency_per_week']
        if frequency is None:
            frequency = edge['assumed_frequency_per_week']
        if edge['mode'] in scheduled and frequency is None:
            raise AssertionError('unknown scheduled frequency needs separate status analysis')
        weight = edge['travel_h'] + (84.0 / frequency if edge['mode'] in scheduled else 0)
        a, b = index[edge['from_id']], index[edge['to_id']]
        d[a][b] = min(d[a][b], weight)
        if edge['bidirectional']:
            d[b][a] = min(d[b][a], weight)
    for k in range(len(points)):
        for i in range(len(points)):
            for j in range(len(points)):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    pairs = {p['id']: p for p in pilot['pairs']}
    rows = []
    for pair in actual['pairs']:
        definition = pairs[pair['pair_id']]
        expected = d[index[definition['from_id']]][index[definition['to_id']]]
        observed = pair['changed']
        if math.isinf(expected):
            assert observed['status'] == 'no_route' and observed['total_h'] is None
            rows.append({'pair': pair['pair_id'], 'status': 'no_route', 'error_h': None})
        else:
            assert observed['status'] == 'found' and observed['total_h'] is not None
            error = abs(expected - observed['total_h'])
            assert error < 1e-9, (season, disabled, pair['pair_id'], error)
            rows.append({'pair': pair['pair_id'], 'status': 'found', 'error_h': error})
    return {'season': season, 'disabled': disabled, 'pairs': rows}

cases = [(season, disabled) for season in ('summer', 'winter') for disabled in sets]
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(check, cases))
flat = [p for row in results for p in row['pairs']]
print(json.dumps({'artifact_version':pilot['artifact_version'], 'requests':len(results),
                  'comparisons':len(flat), 'no_route':sum(p['status']=='no_route' for p in flat),
                  'found':sum(p['status']=='found' for p in flat),
                  'max_absolute_error_h':max(p['error_h'] for p in flat if p['error_h'] is not None),
                  'results':results}, ensure_ascii=False, indent=2, allow_nan=False))
