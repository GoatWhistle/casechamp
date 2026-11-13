import pytest

from app.adapter.normative.walking_graph import WalkingGraph
from app.adapter.transit.walking import TransitWalking
from app.usecase.normative.walking import PedestrianNetwork
from app.usecase.transit_walking import WalkingPoint


def routing() -> TransitWalking:
    network = PedestrianNetwork('test', [(0, 45., 40.), (1, 45., 40.01), (2, 45.01, 40.01)],
                                [(0, 1, 1000., 1), (1, 2, 1000., 2)], 'source', 'today')
    return TransitWalking(WalkingGraph(network, spherical=True), 1.)


def test_access_and_egress_follow_direction_and_include_network_detour() -> None:
    result = routing().measure([WalkingPoint('home', 45., 40., 10.),
                                WalkingPoint('stop', 45.01, 40.01, 10.)],
                               [('home', 'stop'), ('stop', 'home')], 2500.)
    assert result[0].status == 'available'
    assert result[0].metres == pytest.approx(2000.)
    assert result[0].seconds == 2000
    assert result[1].status == 'outside_walking_limit'
    assert result[1].seconds is None


def test_two_points_on_same_edge_use_the_segment_between_them() -> None:
    result = routing().measure([WalkingPoint('a', 45., 40.002, 10.),
                                WalkingPoint('b', 45., 40.008, 10.)], [('a', 'b'), ('b', 'a')], 700.)
    assert result[0].metres == pytest.approx(600.)
    assert result[0].seconds in {600, 601}
    assert result[1].seconds is None


def test_missing_coordinate_and_long_approach_remain_unknown() -> None:
    result = routing().measure([WalkingPoint('known', 45., 40., 10.),
                                WalkingPoint('missing', None, None, 10.),
                                WalkingPoint('far', 46., 41., 10.)],
                               [('known', 'missing'), ('far', 'known')], 2500.)
    assert all(link.status == 'unattached' and link.seconds is None for link in result)


def test_walking_limit_does_not_become_an_unlimited_connector() -> None:
    result = routing().measure([WalkingPoint('a', 45., 40., 10.),
                                WalkingPoint('b', 45.01, 40.01, 10.)], [('a', 'b')], 1500.)
    assert result[0].status == 'outside_walking_limit' and result[0].metres is None
