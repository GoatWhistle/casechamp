import json
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

BASE = 'http://localhost:8081/api/v1/pilots/tuva'
with urlopen(BASE, timeout=5) as response:
    pilot = json.load(response)
edges = [edge for edge in pilot['edges'] if edge['frequency_editable']]

def evaluate(edge, season, frequency):
    data = {'season': season, 'model_version': pilot['model_version'],
            'artifact_version': pilot['artifact_version'],
            'changes': [{'edge_id': edge['id'], 'frequency_per_week': frequency}]}
    request = Request(BASE + '/evaluate', data=json.dumps(data).encode(),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    return {'edge': edge['id'], 'season': season, 'frequency': frequency,
            'pairs': {pair['pair_id']: {'status': pair['changed']['status'],
                                        'total_h': pair['changed']['total_h'],
                                        'baseline_h': pair['baseline']['total_h']}
                      for pair in result['pairs']}}

cases = [(edge, season, frequency) for edge in edges
         for season in ('summer', 'winter') for frequency in range(1, 29)]
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(lambda case: evaluate(*case), cases))
checks = 0
inactive_checks = 0
improvements = []
for edge in edges:
    for season in ('summer', 'winter'):
        subset = [r for r in results if r['edge'] == edge['id'] and r['season'] == season]
        assert len(subset) == 28
        for pair_id in subset[0]['pairs']:
            values = [row['pairs'][pair_id] for row in subset]
            for previous, current in zip(values, values[1:]):
                assert previous['status'] == current['status'], (edge['id'], season, pair_id)
                if previous['total_h'] is not None and current['total_h'] is not None:
                    assert current['total_h'] <= previous['total_h'] + 1e-9, (edge['id'], season, pair_id)
                    checks += 1
            if season not in edge['seasons']:
                for value in values:
                    assert value['total_h'] == value['baseline_h'], (edge['id'], season, pair_id)
                    inactive_checks += 1
            first, last = values[0]['total_h'], values[-1]['total_h']
            if first is not None and last is not None and last < first - 1e-9:
                improvements.append({'edge': edge['id'], 'season': season, 'pair': pair_id,
                                     'one_per_week_h': first, 'twenty_eight_per_week_h': last})
print(json.dumps({'model_version': pilot['model_version'], 'artifact_version': pilot['artifact_version'],
                  'requests': len(results), 'adjacent_numeric_checks': checks,
                  'inactive_season_checks': inactive_checks, 'improvements': improvements,
                  'results': results}, ensure_ascii=False, indent=2, allow_nan=False))
