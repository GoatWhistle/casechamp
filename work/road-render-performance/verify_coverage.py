import json
import urllib.request
from itertools import pairwise
from pathlib import Path


def edges(segments: list[dict]) -> set[tuple]:
    return {
        (road['way_id'], tuple(sorted((tuple(a), tuple(b)))))
        for road in segments for a, b in pairwise(road['coordinates'])
    }


with urllib.request.urlopen('http://127.0.0.1:8001/api/v1/road-graph?west=38&south=54&east=43&north=57&zoom=7') as response:
    after = json.load(response)
before = json.loads(Path('/private/tmp/plexus-road-baseline.json').read_text())
old_edges, new_edges = edges(before['segments']), edges(after['segments'])
assert old_edges <= new_edges, f'{len(old_edges-new_edges)} original edges missing'
assert {r['way_id'] for r in before['segments']} == {r['way_id'] for r in after['segments']}
result = {'old_edges': len(old_edges), 'new_edges': len(new_edges), 'missing_edges': len(old_edges-new_edges), 'same_way_ids': True}
Path('work/road-render-performance/coverage.json').write_text(json.dumps(result,indent=2))
print(result)
