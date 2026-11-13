import json
import sys

import pytest

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


def test_cross_border_batch_replaces_legacy_and_does_not_skip_empty_local_catalog(tmp_path, monkeypatch):
    regions, output = tmp_path / 'regions.json', tmp_path / 'results.json'
    regions.write_text(json.dumps({'regions': [{'id': '07000000', 'name': 'region'}]}))
    output.write_text(json.dumps([{'region_id': '07000000', 'criterion_id': 'N01',
                                  'status': 200, 'model_revision': 'regional-road-v1'}]))
    receipt = {'run_id': 'new', 'origins': 2, 'measured_paths': 2, 'mode': 'car',
               'unit': 'minutes', 'facilities': 1, 'qualification': 'physical_only',
               'graph_revision': 'graph', 'closed_way_ids': [], 'model_revision': 'new-model'}
    posts = []

    def request(url, method='GET', command=None):
        if '/catalog/' in url:
            return 200, {'candidate_count': 0}
        if method == 'GET':
            return 200, {**receipt, 'model_revision': 'regional-road-v1'}
        posts.append(command)
        return 200, receipt

    monkeypatch.setattr(batch, 'request', request)
    monkeypatch.setattr(sys, 'argv', ['batch', '--regions', str(regions), '--output', str(output),
                                    '--criteria', 'N01', '--resume', '--required-model-revision', 'new-model'])
    batch.main()
    assert len(posts) == 1
    assert json.loads(output.read_text())[-1]['model_revision'] == 'new-model'
    batch.main()
    assert len(posts) == 1


def test_batch_rejects_a_success_response_from_the_wrong_model(tmp_path, monkeypatch):
    regions, output = tmp_path / 'regions.json', tmp_path / 'results.json'
    regions.write_text(json.dumps({'regions': [{'id': '03000000', 'name': 'region'}]}))
    monkeypatch.setattr(batch, 'request', lambda url, *args: (
        200, {'candidate_count': 1} if '/catalog/' in url else {'model_revision': 'legacy'}
    ))
    monkeypatch.setattr(sys, 'argv', ['batch', '--regions', str(regions), '--output', str(output),
                                    '--criteria', 'N01', '--required-model-revision', 'new-model'])
    with pytest.raises(SystemExit, match='batch incomplete'):
        batch.main()
    record = json.loads(output.read_text())[-1]
    assert record['status'] == 409
    assert record['error']['code'] == 'measurement_model_revision_mismatch'
