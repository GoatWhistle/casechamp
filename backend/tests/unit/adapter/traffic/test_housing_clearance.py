import numpy as np
from synthetic_traffic.demand import xyz
from synthetic_traffic.model import Network

from app.adapter.traffic.housing_clearance import clear_segment


def test_new_connection_cannot_cut_through_a_residential_corridor() -> None:
    network = Network(
        np.array([0, 1]),
        np.array([1, 0]),
        np.array([0.1, 0.1]),
        np.array([1800.0, 1800.0]),
        np.array([1.0, 1.0]),
        np.array([1, 1]),
        np.array([10, 20]),
        np.array([44.0, 44.0]),
        np.array([42.0, 42.02]),
        np.array([-1, -1]),
    )
    project = {"source_node": 10, "target_node": 20}
    blocked = xyz(np.array([44.0]), np.array([42.01]))
    clear = xyz(np.array([44.01]), np.array([42.01]))
    assert not clear_segment(network, project, blocked, np.array([0.04]))
    assert clear_segment(network, project, clear, np.array([0.04]))
    assert not clear_segment(network, project, np.empty((0, 3)), np.array([]))
