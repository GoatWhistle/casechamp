import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = 'http://localhost:8081/api/v1/pilots/tuva'
with urlopen(base, timeout=5) as response:
    pilot = json.load(response)

def post(changes, version=None):
    body = {'season': 'summer', 'model_version': pilot['model_version'],
            'artifact_version': version or pilot['artifact_version'], 'changes': changes}
    request = Request(base + '/evaluate', data=json.dumps(body).encode(),
                      headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)

baseline_status, baseline = post([])
assert baseline_status == 200
cases = {
    'duplicate_enabled_disabled': ([{'edge_id': 'manual:0', 'enabled': True}, {'edge_id': 'manual:0', 'enabled': False}], None, 422),
    'duplicate_reversed': ([{'edge_id': 'manual:0', 'enabled': False}, {'edge_id': 'manual:0', 'enabled': True}], None, 422),
    'duplicate_frequency': ([{'edge_id': 'manual:0', 'frequency_per_week': 2}, {'edge_id': 'manual:0', 'frequency_per_week': 7}], None, 422),
    'unknown_edge': ([{'edge_id': 'no-such-edge', 'enabled': False}], None, 422),
    'derived_road': ([{'edge_id': next(e['id'] for e in pilot['edges'] if not e['editable']), 'enabled': False}], None, 422),
    'winter_road_frequency': ([{'edge_id': 'manual:5', 'frequency_per_week': 7}], None, 422),
    'stale_version': ([{'edge_id': 'manual:0', 'frequency_per_week': 7}], 'outdated-test-version', 409),
}
results = {}
for name, (changes, version, expected) in cases.items():
    status, body = post(changes, version)
    assert status == expected, (name, status, body)
    results[name] = {'status': status, 'code': body.get('code')}
status, after = post([])
assert status == 200 and after == baseline
print(json.dumps({'model_version':pilot['model_version'],'artifact_version':pilot['artifact_version'],
                  'cases':results,'baseline_unchanged_after_invalid_requests':True}, ensure_ascii=False, indent=2))
