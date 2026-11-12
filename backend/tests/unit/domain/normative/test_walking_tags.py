import pytest

from app.domain.normative.walking import (
    blocked_node,
    metres_between,
    residential,
    walkable,
    walking_directions,
)


@pytest.mark.parametrize("highway", ["motorway", "trunk", "construction", "proposed"])
def test_vehicle_only_and_unbuilt_ways_are_not_pedestrian_links(highway: str) -> None:
    assert not walkable({"highway": highway})


def test_explicit_foot_access_has_precedence_over_generic_access() -> None:
    assert walkable({"highway": "service", "access": "private", "foot": "yes"})
    assert not walkable({"highway": "footway", "access": "yes", "foot": "no"})
    assert not walkable({"highway": "residential", "access": "private"})


def test_unresolved_conditional_access_is_not_silently_assumed_open() -> None:
    assert not walkable({"highway": "path", "foot:conditional": "no @ (winter)"})


def test_motor_vehicle_one_way_does_not_block_reverse_walking() -> None:
    assert walking_directions({"oneway": "yes"}) == (True, True)
    assert walking_directions({"oneway:foot": "yes"}) == (True, False)
    assert walking_directions({"oneway:foot": "-1"}) == (False, True)


def test_locked_and_private_barriers_do_not_create_false_shortcuts() -> None:
    assert blocked_node({"barrier": "gate", "locked": "yes"})
    assert blocked_node({"barrier": "gate", "locked": "yes", "foot": "yes"})
    assert blocked_node({"barrier": "gate", "access": "private"})
    assert not blocked_node({"barrier": "gate", "access": "private", "foot": "yes"})
    assert not blocked_node({"barrier": "bollard"})


def test_unclassified_buildings_are_not_invented_as_residential() -> None:
    assert residential({"building": "apartments"})
    assert residential({"building": "yes", "building:use": "residential"})
    assert not residential({"building": "yes"})
    assert not residential({"building": "school"})


def test_network_distance_uses_metres_and_keeps_identical_coordinates_at_zero() -> None:
    assert metres_between((65, 55), (65, 55)) == 0
    assert metres_between((65, 55), (65, 55.001)) == pytest.approx(111.195, abs=0.01)
