import argparse
import gzip
import json
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:8001')
parser.add_argument('--output', required=True)
args = parser.parse_args()
request = urllib.request.Request(
    args.base + '/api/v1/road-graph?west=38&south=54&east=43&north=57&zoom=7',
    headers={'Accept-Encoding': 'gzip'},
)
started = time.perf_counter()
with urllib.request.urlopen(request, timeout=60) as response:
    body = response.read()
    wire_bytes = len(body)
    if response.headers.get('Content-Encoding') == 'gzip':
        body = gzip.decompress(body)
elapsed = time.perf_counter() - started
view = json.loads(body)
result = {
    'seconds': elapsed,
    'wire_bytes': wire_bytes,
    'decoded_bytes': len(body),
    'features': len(view['segments']),
    'vertices': sum(len(road['coordinates']) for road in view['segments']),
    'ways': len({road['way_id'] for road in view['segments']}),
    'matched': view['matched'],
    'detail': view['detail'],
}
with open(args.output, 'w') as file:
    json.dump(result, file, indent=2)
print(json.dumps(result))
assert elapsed < 2, f'Road viewport took {elapsed:.2f}s; budget is 2s'
assert len(body) < 8_000_000, 'Viewport payload exceeds 8MB decoded'
