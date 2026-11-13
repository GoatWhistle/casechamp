from app.adapter.normative.walking_graph import WalkingGraph
from app.adapter.transit.walking import TransitWalking
from app.domain.transit_journey import TransitConnection
from app.usecase.normative.walking import PedestrianNetwork
from app.usecase.transit_access import TransitAccess
from app.usecase.transit_walking import WalkingPoint


def points() -> tuple[WalkingPoint, WalkingPoint, list[WalkingPoint]]:
    return (WalkingPoint('home', 45., 40., 10.), WalkingPoint('clinic', 45., 41.001, 10.),
            [WalkingPoint('A', 45., 40.001, 10.), WalkingPoint('B', 45., 41., 10.)])


def access() -> TransitAccess:
    network = PedestrianNetwork('two-towns', [(0, 45., 40.), (1, 45., 40.001),
                                             (2, 45., 41.), (3, 45., 41.001)],
                                [(0, 1, 140., 1), (2, 3, 280., 2)], 'source', 'today')
    return TransitAccess(TransitWalking(WalkingGraph(network, spherical=True)))


def test_combines_real_graph_approaches_with_waiting_and_bus() -> None:
    origin, destination, stops = points()
    result = access().run(origin, destination, stops, [TransitConnection('bus', 'A', 'B', 600, 1200)], 0, 3600)
    assert result.status == 'available' and result.journey is not None
    assert result.journey.arrival == 1400
    assert [leg.mode for leg in result.journey.legs] == ['walk', 'wait', 'bus', 'walk']
    assert result.journey.legs[0].source == 'home'
    assert result.journey.legs[-1].target == 'clinic'
    assert result.journey.boardings == 1
    assert result.walking_revision == 'two-towns'
    assert result.coverage_complete is False


def test_unlocated_alighting_stop_is_unknown_coverage_not_isolation() -> None:
    origin, destination, stops = points()
    stops[1] = WalkingPoint('B', None, None, 10.)
    result = access().run(origin, destination, stops, [TransitConnection('bus', 'A', 'B', 600, 1200)], 0, 3600)
    assert result.status == 'no_journey_in_covered_data' and result.journey is None
    assert result.stops_without_coordinates == 1
    assert result.timetable_stops_without_coordinates == 1


def test_direct_walking_is_not_forced_onto_a_bus() -> None:
    origin, _, stops = points()
    destination = WalkingPoint('nearby', 45., 40.0005, 10.)
    result = access().run(origin, destination, stops, [], 0, 3600)
    assert result.journey is not None and result.journey.boardings == 0
    assert result.journey.arrival in {50, 51}
    assert len(result.journey.legs) == 1
