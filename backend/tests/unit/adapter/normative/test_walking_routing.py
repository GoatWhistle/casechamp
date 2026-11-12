from dataclasses import replace

import pytest

from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.domain.errors import DataUnavailable
from app.domain.normative.model import Facility, Origin, coverage
from app.usecase.normative.walking import PedestrianNetwork


class NetworkRepository:
    def network(self, revision: str | None = None) -> PedestrianNetwork:
        return PedestrianNetwork(
            "walking-test",
            [(0, 55, 65), (1, 55, 65.0001), (2, 55, 65.0002), (3, 55.0001, 65.0001)],
            [(0, 1, 10, 10), (0, 1, 15, 11), (1, 2, 10, 12), (1, 3, 10, 13)],
            "https://example.org/pbf",
            "2026-11-11",
        )


def facility() -> Facility:
    return Facility(
        "school",
        "school",
        "School",
        "Address",
        "https://example.org",
        "2026-11-12",
        55,
        65.0002,
        "https://example.org",
        "official_institution_pin",
    )


def origin(node: int = 0) -> Origin:
    coords = NetworkRepository().network().nodes[node]
    return Origin(str(node), "Building", None, None, None, coords[1], coords[2])


def test_pedestrian_direction_is_from_residence_to_target_not_the_reverse() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    result = routing.evaluate([origin(), origin(3)], [facility()], 500, [])
    assert result[0].distance_metres == pytest.approx(20)
    assert result[1].distance_metres is None
    assert "path_unconfirmed" in result[1].uncertainty


def test_closing_parallel_foot_link_keeps_the_alternative_with_its_own_distance() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    before = routing.evaluate([origin()], [facility()], 500, [])
    after = routing.evaluate([origin()], [facility()], 500, [10])
    assert before[0].distance_metres == pytest.approx(20)
    assert after[0].distance_metres == pytest.approx(25)


def test_short_reference_path_does_not_invent_children_or_legal_compliance() -> None:
    result = WalkingNormativeRouting(NetworkRepository()).evaluate(
        [origin()], [facility()], 500, []
    )
    assert result[0].state == "unknown"
    assert result[0].population is None
    assert result[0].minutes is None
    assert result[0].excess_minutes is None
    assert "population_group_missing" in result[0].uncertainty
    assert coverage(result).lower_percent is None
    assert coverage(result).unknown_population_points == 1


def test_a_distant_building_is_not_connected_by_a_fictitious_long_connector() -> None:
    far = Origin("far", "Far", None, None, None, 55.5, 65)
    row = WalkingNormativeRouting(NetworkRepository()).evaluate([far], [facility()], 500, [])[0]
    assert row.distance_metres is None
    assert "origin_unattached" in row.uncertainty


def test_closing_all_forward_links_cannot_create_an_accessible_route() -> None:
    row = WalkingNormativeRouting(NetworkRepository()).evaluate(
        [origin()],
        [facility()],
        500,
        [10, 11],
    )[0]
    assert row.distance_metres is None
    assert row.state == "unknown"


def test_trace_reconstructs_saved_directed_cost_and_marks_assumed_approaches() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    row = routing.evaluate([origin()], [facility()], 500, [10])[0]
    assert row.routing_node is not None and row.approach_metres is not None
    frozen = Origin(
        row.id,
        row.name,
        None,
        row.routing_node,
        row.approach_metres / 1000,
        row.latitude,
        row.longitude,
    )
    route = routing.trace(frozen, facility(), [10], "walking-test")
    assert route.distance_metres == pytest.approx(row.distance_metres)
    assert route.network_coordinates == [(65, 55), (65.0001, 55), (65.0002, 55)]
    assert len(route.approaches) == 2
    assert routing.missing_ways([10, 999]) == [999]


def test_trace_does_not_invent_a_path_after_closure() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    frozen = Origin("0", "Building", None, 0, 0, 55, 65)
    with pytest.raises(DataUnavailable):
        routing.trace(frozen, facility(), [10, 11], "walking-test")


def test_verified_entrances_do_not_keep_the_proxy_entrance_warning() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    building = replace(origin(), entrance_verified=True)
    target = replace(facility(), coordinate_status="verified_entrance")
    result = routing.evaluate([building], [target], 500, [])[0]
    assert "residential_reference_not_entrance" not in result.uncertainty
    assert "facility_entrances_unverified" not in result.uncertainty
    assert "population_group_missing" in result.uncertainty


class LongStreetRepository:
    def __init__(self, both_ways: bool = True) -> None:
        self.both_ways = both_ways

    def network(self, revision: str | None = None) -> PedestrianNetwork:
        forward = [(0, 1, 319.0, 20)]
        backward = [(1, 0, 319.0, 21)] if self.both_ways else []
        return PedestrianNetwork(
            "long-street",
            [(0, 55, 65), (1, 55, 65.005)],
            forward + backward,
            "https://example.org/pbf",
            "2026-11-12",
        )


def school_at(latitude: float, longitude: float) -> Facility:
    return replace(facility(), latitude=latitude, longitude=longitude)


def test_a_school_beside_the_middle_of_a_long_street_is_reachable() -> None:
    routing = WalkingNormativeRouting(LongStreetRepository())
    start = Origin("start", "Building", None, None, None, 55, 65)
    row = routing.evaluate([start], [school_at(55.0002, 65.0025)], 500, [])[0]
    assert row.distance_metres == pytest.approx(159.5 + 22.2, abs=1.5)


def test_a_building_beside_a_long_street_attaches_to_the_street_not_a_far_vertex() -> None:
    routing = WalkingNormativeRouting(LongStreetRepository())
    middle = Origin("middle", "Building", None, None, None, 55.0002, 65.0025)
    row = routing.evaluate([middle], [school_at(55, 65.005)], 500, [])[0]
    assert "origin_unattached" not in row.uncertainty
    assert row.distance_metres == pytest.approx(22.2 + 159.5, abs=1.5)


def test_walking_along_a_one_way_segment_respects_its_direction() -> None:
    routing = WalkingNormativeRouting(LongStreetRepository(both_ways=False))
    middle = Origin("middle", "Building", None, None, None, 55.0002, 65.0025)
    row = routing.evaluate([middle], [school_at(55, 65)], 500, [])[0]
    assert row.distance_metres is None


def test_closing_the_attached_segment_removes_the_access_along_it() -> None:
    routing = WalkingNormativeRouting(LongStreetRepository())
    start = Origin("start", "Building", None, None, None, 55, 65)
    target = school_at(55.0002, 65.0025)
    assert routing.evaluate([start], [target], 500, [20, 21])[0].distance_metres is None


def test_a_school_far_from_every_street_is_not_attached() -> None:
    routing = WalkingNormativeRouting(LongStreetRepository())
    start = Origin("start", "Building", None, None, None, 55, 65)
    with pytest.raises(DataUnavailable):
        routing.evaluate([start], [school_at(55.003, 65.0025)], 500, [])
