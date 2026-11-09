import json
import math
from pathlib import Path
from urllib.request import urlopen

with urlopen('http://localhost:8081/api/v1/pilots/tuva', timeout=5) as response:
    pilot = json.load(response)
sweep = json.loads(Path('work/experiments/pilot-frequency-sweep.json').read_text())
assert sweep['artifact_version'] == pilot['artifact_version']
points = [point['id'] for point in pilot['points']]
pairs = {pair['id']: pair for pair in pilot['pairs']}
assert len(points) == len(set(points))
index = {point: position for position, point in enumerate(points)}
scheduled = {'air', 'river', 'scheduled_ferry', 'rail'}
max_error = 0.0
comparisons = 0
for case in sweep['results']:
    distances = [[math.inf] * len(points) for _ in points]
    for i in range(len(points)):
        distances[i][i] = 0.0
    for edge in pilot['edges']:
        if case['season'] not in edge['seasons']:
            continue
        wait = 0.0
        if edge['mode'] in scheduled:
            frequency = (case['frequency'] if edge['id'] == case['edge'] else
                         edge['frequency_per_week'] if edge['frequency_per_week'] is not None else
                         edge['assumed_frequency_per_week'])
            if frequency is None:
                continue
            wait = 84.0 / frequency
        a, b = index[edge['from_id']], index[edge['to_id']]
        weight = edge['travel_h'] + wait
        distances[a][b] = min(distances[a][b], weight)
        if edge['bidirectional']:
            distances[b][a] = min(distances[b][a], weight)
    for k in range(len(points)):
        for i in range(len(points)):
            for j in range(len(points)):
                distances[i][j] = min(distances[i][j], distances[i][k] + distances[k][j])
    for pair_id, observed in case['pairs'].items():
        pair = pairs[pair_id]
        expected = distances[index[pair['from_id']]][index[pair['to_id']]]
        assert observed['status'] == 'found' and observed['total_h'] is not None
        error = abs(expected - observed['total_h'])
        assert error < 1e-9, (case['edge'], case['season'], case['frequency'], pair_id, error)
        max_error = max(max_error, error)
        comparisons += 1
assert comparisons == 1008
print(json.dumps({'algorithm': 'Floyd-Warshall on API graph with fixed 84/f waiting',
                  'artifact_version': pilot['artifact_version'], 'scenarios': len(sweep['results']),
                  'pair_comparisons': comparisons, 'max_absolute_error_h': max_error,
                  'limitation': 'same stored graph and weights; no external data validation'}, indent=2))
