from dataclasses import replace

import numpy as np
from synthetic_traffic.baseline_store import load_baseline, save_baseline
from synthetic_traffic.incremental import evaluate_incremental, prepare_incremental
from synthetic_traffic.incremental_paths import PathCache
from synthetic_traffic.model import Trip
from synthetic_traffic.tree_store import ArchiveTrees, TreeStore
from test_synthetic_traffic import network as make_network
from test_traffic_incremental import network


def test_disk_trees_match_memory_assignment_and_saved_scenario(tmp_path):
    graph = network()
    trips = [Trip(0, 4, 2.), Trip(2, 3, 1.), Trip(4, 1, 1.)]
    memory = prepare_incremental(graph, trips)
    disk = prepare_incremental(graph, trips, tree_directory=tmp_path / 'trees')
    assert isinstance(disk.paths.trees, TreeStore)
    assert len(list((tmp_path / 'trees').glob('*.npz'))) == 3
    np.testing.assert_allclose(memory.assignment.flow, disk.assignment.flow)
    save_baseline(disk, tmp_path / 'published')
    restored = load_baseline(tmp_path / 'published')
    assert isinstance(restored.paths.trees, ArchiveTrees)
    before = restored.paths.trees[0].distance.copy()
    changed = replace(graph, capacity=graph.capacity * 2)
    expected = evaluate_incremental(memory, changed)
    actual = evaluate_incremental(restored, changed)
    np.testing.assert_allclose(actual.flow, expected.flow)
    np.testing.assert_allclose(actual.hours, expected.hours)
    np.testing.assert_array_equal(restored.paths.trees[0].distance, before)


def test_disk_tree_fork_does_not_modify_original(tmp_path):
    graph = network()
    baseline = prepare_incremental(graph, [Trip(0, 4, 1.)], tree_directory=tmp_path / 'trees')
    fork = baseline.paths.fork()
    before = baseline.paths.trees[0].distance.copy()
    fork.update(graph, baseline.assignment.hours * 3)
    np.testing.assert_allclose(fork.trees[0].distance, before * 3)
    np.testing.assert_array_equal(baseline.paths.trees[0].distance, before)


def test_limited_tree_expands_for_a_longer_detour_and_survives_publication(tmp_path):

    graph = make_network((0, 1, 0, 2), (1, 3, 2, 3), (1., 1., 5., 1.), (1800.,) * 4)
    paths = PathCache(graph, [Trip(0, 3, 10.)], graph.free_hours,
                      tree_directory=tmp_path / 'limited', path_limit=3.)
    assert not np.isfinite(paths.trees[0].distance[2])
    changed = replace(graph, free_hours=np.array([1., 10., 5., 1.]))
    paths.update(changed, changed.free_hours)
    flow, missing, times = paths.load(changed)
    assert times == [6.]
    assert missing == 0
    np.testing.assert_array_equal(flow, [0., 0., 10., 10.])
    assert paths.trees[0].limit == 6.


def test_limited_tree_finds_new_shortcut_outside_cached_radius(tmp_path):

    graph = make_network((0, 1, 0, 2), (1, 3, 2, 3), (1., 1., 5., 0.5), (1800.,) * 4)
    paths = PathCache(graph, [Trip(0, 3, 10.)], graph.free_hours,
                      tree_directory=tmp_path / 'limited', path_limit=3.)
    changed = replace(graph, free_hours=np.array([1., 1., 0.5, 0.5]))
    paths.update(changed, changed.free_hours)
    flow, missing, times = paths.load(changed)
    assert times == [1.]
    assert missing == 0
    np.testing.assert_array_equal(flow, [0., 0., 10., 10.])
