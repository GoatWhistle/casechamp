import numpy as np

from app.adapter.road_corridor.band import band_pairs
from app.adapter.road_corridor.gaps import gap_pairs


def test_parallel_carriageways_are_joined_without_detour_to_far_end() -> None:
    lat = np.linspace(56.0, 57.0, 11)
    west = np.column_stack([np.full(11, 36.0), lat])
    east = np.column_stack([np.full(11, 36.001), lat])
    xy = np.vstack([west, east])
    ids = np.arange(22)
    pairs = [(i, i + 1) for i in range(10)] + [(11 + i, 12 + i) for i in range(10)] + [(0, 11)]
    selected = band_pairs(ids, xy, pairs, 15, 20, 0.5)
    assert (5, 6) in selected and (15, 16) in selected
    assert (0, 1) not in selected and (0, 11) not in selected


def test_gaps_connect_nearest_nodes_of_separate_pieces_only_within_limit() -> None:
    xy = np.array([[36.0, 56.0], [36.0, 56.1], [36.0, 56.13], [36.0, 56.3], [36.0, 58.0]])
    ids = np.arange(5)
    labels = np.array([0, 0, 1, 1, 2])
    assert gap_pairs(ids, xy, labels, [(0, 1), (2, 3)], 5.0) == [(1, 2)]
