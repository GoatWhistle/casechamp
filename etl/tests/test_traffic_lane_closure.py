import numpy as np
import pytest

from synthetic_traffic.model import Network
from synthetic_traffic.projects import apply_project


def network(capacity=3600., shared=-1):
    return Network(np.array([0, 1, 1]), np.array([1, 0, 2]), np.ones(3),
                   np.array([capacity, 3600., 1800.]), np.ones(3), np.array([10, 10, 20]),
                   np.arange(3), np.zeros(3), np.zeros(3), np.array([shared, shared, -1]))


def test_one_lane_closure_changes_only_selected_direction_without_mutating_baseline():
    before = network()
    after = apply_project(before, {'kind': 'lane_closure', 'way_ids': [10], 'edge_indices': [0]})
    np.testing.assert_array_equal(after.capacity, [1800, 3600, 1800])
    np.testing.assert_array_equal(before.capacity, [3600, 3600, 1800])
    np.testing.assert_array_equal(after.free_hours, before.free_hours)
    np.testing.assert_array_equal(after.source, before.source)


def test_last_lane_removes_only_chosen_direction():
    before = network(capacity=1800)
    after = apply_project(before, {'kind': 'lane_closure', 'way_ids': [10], 'edge_indices': [0]})
    assert list(zip(after.source, after.target, strict=True)) == [(1, 0), (1, 2)]
    np.testing.assert_array_equal(before.source, [0, 1, 1])


def test_full_local_closure_leaves_other_segments_available():
    after = apply_project(network(), {'kind': 'closure', 'way_ids': [10], 'edge_indices': [0, 1]})
    np.testing.assert_array_equal(after.way_id, [20])


@pytest.mark.parametrize('project', [
    {'kind': 'lane_closure', 'way_ids': [10]},
    {'kind': 'lane_closure', 'way_ids': [10], 'edge_indices': [2]},
])
def test_lane_closure_rejects_ambiguous_or_foreign_edges(project):
    with pytest.raises(ValueError):
        apply_project(network(), project)


def test_shared_lane_cannot_be_closed_in_one_direction():
    with pytest.raises(ValueError, match='shared lane'):
        apply_project(network(shared=0), {'kind': 'lane_closure', 'way_ids': [10], 'edge_indices': [0]})


def test_lane_addition_changes_only_selected_direction_and_preserves_baseline():
    before = network()
    after = apply_project(before, {'kind': 'capacity', 'way_ids': [10], 'edge_indices': [1], 'extra_lanes': 1})
    np.testing.assert_array_equal(after.capacity, [3600, 5400, 1800])
    np.testing.assert_array_equal(before.capacity, [3600, 3600, 1800])
    np.testing.assert_array_equal(after.free_hours, before.free_hours)
