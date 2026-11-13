from dataclasses import replace

import numpy as np
import pytest
from synthetic_traffic.baseline_store import load_baseline, save_baseline
from synthetic_traffic.incremental import evaluate_incremental, prepare_incremental
from synthetic_traffic.model import Trip
from synthetic_traffic.projects import apply_project
from test_synthetic_traffic import network
from test_traffic_incremental import network as loop_network


def test_saved_baseline_restores_without_shortest_path_construction(tmp_path, monkeypatch):
    graph = network((0,), (1,), (1.0,), (1800.0,))
    baseline = prepare_incremental(graph, [Trip(0, 1, 2000)])
    path = tmp_path / "baseline"
    save_baseline(baseline, path)
    def forbidden(*args, **kwargs):
        raise AssertionError("Baseline was recomputed")
    monkeypatch.setattr("synthetic_traffic.incremental_paths.dijkstra", forbidden)
    restored = load_baseline(path)
    np.testing.assert_array_equal(restored.assignment.flow, baseline.assignment.flow)
    np.testing.assert_array_equal(restored.paths.trees[0].distance, baseline.paths.trees[0].distance)
    result = evaluate_incremental(restored, replace(graph, capacity=graph.capacity * 2))
    assert result.converged
    assert result.hours[0] < baseline.assignment.hours[0]
    np.testing.assert_array_equal(restored.assignment.flow, baseline.assignment.flow)
    with pytest.raises(FileExistsError):
        save_baseline(restored, path)


def test_corrupt_and_unconverged_baselines_are_rejected(tmp_path):
    baseline = prepare_incremental(network(), [Trip(0, 3, 1)])
    with pytest.raises(ValueError, match="converged"):
        save_baseline(replace(baseline, assignment=replace(baseline.assignment, converged=False)), tmp_path / "bad")
    path = tmp_path / "good"
    save_baseline(baseline, path)
    (path / "arrays.npz").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        load_baseline(path)


def test_closure_restores_origin_flows_and_repairs_without_dijkstra(tmp_path, monkeypatch):

    graph = loop_network()
    baseline = prepare_incremental(graph, [Trip(0, 4, 1.0), Trip(2, 3, 1.0)])
    assert baseline.assignment.converged
    total = np.zeros(len(graph.source))
    for values in baseline.origin_flows.values():
        for edge, amount in values.items():
            total[edge] += amount
    np.testing.assert_allclose(total, baseline.assignment.flow)
    save_baseline(baseline, tmp_path / 'closure')
    restored = load_baseline(tmp_path / 'closure')
    assert restored.origin_flows == baseline.origin_flows

    def forbidden(*args, **kwargs):
        raise AssertionError('Closure rebuilt shortest path trees')

    monkeypatch.setattr('synthetic_traffic.incremental_paths.dijkstra', forbidden)
    keep = np.arange(1, len(graph.source))
    changed = replace(graph, **{
        key: getattr(graph, key)[keep]
        for key in ('source', 'target', 'free_hours', 'capacity', 'length_km', 'way_id', 'shared')
    })
    result = evaluate_incremental(restored, changed)
    assert result.converged
    assert result.unserved_vehicles_per_hour == 0
    assert result.flow[0] == pytest.approx(1)
    np.testing.assert_array_equal(restored.assignment.flow, baseline.assignment.flow)


def test_selected_segments_do_not_close_the_rest_of_the_same_way():
    graph = network((0, 1, 2), (1, 2, 3), (1., 1., 1.), (1800., 1800., 1800.))
    graph = replace(graph, way_id=np.array([100, 100, 100]))
    changed = apply_project(graph, {'kind': 'closure', 'way_ids': [100], 'edge_indices': [1]})
    np.testing.assert_array_equal(changed.source, [0, 2])
    np.testing.assert_array_equal(changed.target, [1, 3])
