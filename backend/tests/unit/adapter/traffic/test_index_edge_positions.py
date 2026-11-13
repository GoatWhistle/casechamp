from dataclasses import replace

import numpy as np
import pytest
from tests.unit.adapter.traffic.test_index_delta import make_network

from app.adapter.traffic.index_edge_positions import traffic_edge_positions
from app.domain.errors import InvalidQuery


def test_matches_raw_nodes_and_internal_road_ids_with_last_duplicate() -> None:
    network = replace(make_network(), raw_nodes=np.arange(5) * 10 + 100)
    edges = {
        'src': np.r_[network.raw_nodes[network.source], 100],
        'dst': np.r_[network.raw_nodes[network.target], 110],
        'way_idx': np.r_[np.arange(5) + 90, 90],
    }
    ways = {int(way): 90 + index for index, way in enumerate(network.way_id)}
    positions = traffic_edge_positions(edges, network, ways, 200)
    np.testing.assert_array_equal(positions, [5, 1, 2, 3, 4])


def test_unmatched_real_roads_are_rejected_and_virtual_edges_are_unowned() -> None:
    network = make_network()
    edges = {'src': network.source, 'dst': network.target, 'way_idx': np.arange(5)}
    ways = {int(way): index for index, way in enumerate(network.way_id)}
    with pytest.raises(InvalidQuery):
        traffic_edge_positions(edges, network, {}, 5)
    with pytest.raises(InvalidQuery):
        traffic_edge_positions({**edges, 'src': network.source + 1}, network, ways, 5)
    virtual = replace(network, way_id=np.r_[-1, network.way_id[1:]])
    np.testing.assert_array_equal(traffic_edge_positions(edges, virtual, ways, 5), [-1, 1, 2, 3, 4])
