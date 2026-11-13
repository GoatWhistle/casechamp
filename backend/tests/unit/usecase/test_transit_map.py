from dataclasses import replace

from tests.unit.controller.test_transit_http import queries

from app.usecase.transit_map import transit_map_target


def test_missing_or_invalid_coordinates_are_not_invented_for_map() -> None:
    plan = queries().plan('R', 'home', 'clinic', 0)
    plan = replace(plan, origin=replace(plan.origin, latitude=None),
                   destination=replace(plan.destination, longitude=float('nan')))
    target = transit_map_target('R', plan)
    assert {point.role for point in target.points} == {'stop'}
    assert target.geometry_status == 'stops_only_not_route_geometry'


def test_no_journey_shows_endpoints_without_unrelated_stops() -> None:
    plan = queries().plan('R', 'home', 'clinic', 0)
    plan = replace(plan, result=replace(plan.result, journey=None))
    target = transit_map_target('R', plan)
    assert [point.role for point in target.points] == ['origin', 'destination']
