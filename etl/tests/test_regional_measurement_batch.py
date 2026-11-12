import json
import sys

import calculate_regional_measurements as batch


def test_fire_batch_recalculates_when_speed_changes(tmp_path, monkeypatch):
    regions = tmp_path / 'regions.json'
    output = tmp_path / 'results.json'
    regions.write_text(json.dumps({'regions': [{'id': '07000000', 'name': 'region'}]}))
    output.write_text(json.dumps([{
        'region_id': '07000000', 'criterion_id': 'N03',
        'status': 200, 'fire_speed_kmh': 30,
    }]))
    calls = []
    receipt = {
        'run_id': 'new-run', 'origins': 2, 'measured_paths': 1,
        'mode': 'emergency_response', 'unit': 'minutes', 'facilities': 1,
        'qualification': 'physical_only', 'graph_revision': 'graph-v1',
        'closed_way_ids': [],
    }

    def request(url, method='GET', command=None):
        calls.append((url, method, command))
        return 200, {'candidate_count': 1} if '/catalog/' in url else receipt

    monkeypatch.setattr(batch, 'request', request)
    monkeypatch.setattr(sys, 'argv', [
        'batch', '--regions', str(regions), '--output', str(output),
        '--criteria', 'N03', '--resume', '--fire-speed-kmh', '40',
    ])
    batch.main()
    posts = [call for call in calls if call[1] == 'POST']
    assert len(posts) == 1
    assert posts[0][2]['fire_profile']['speed_kmh'] == 40
    assert 'unverified' in posts[0][2]['fire_profile']['assumption']
    assert json.loads(output.read_text())[-1]['fire_speed_kmh'] == 40
    calls.clear()
    batch.main()
    assert calls == []
