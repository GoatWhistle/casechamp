from copy import deepcopy

import pytest
from publish_transit import build_rows
from test_transit_timetable import rows
from transit_timetable import normalize_timetables


def data():
    source = rows()
    for row in source:
        row['stop_region_code'] = '23'
    timetable = normalize_timetables(source)
    pins = [{'stop_registry_id': 'A', 'coordinate_status': 'official_operator_pin',
             'latitude': 45., 'longitude': 39., 'source_url': 'https://example.org/station',
             'source_sha256': 'abc'},
            {'stop_registry_id': 'B', 'coordinate_status': 'historical_official_route_stop',
             'latitude': 45.1, 'longitude': 39.1}]
    regions = [{'stop_region_code': '23', 'atlas_region_id': '03000000'}]
    return timetable, pins, regions


def test_publication_keeps_unknown_coordinate_and_positional_connections():
    timetable, pins, regions = data()
    stops, connections = build_rows(timetable, pins, regions, 'snapshot')
    assert stops[0]['region_id'] == '03000000' and stops[0]['latitude'] == 45.
    assert stops[1]['latitude'] is None and stops[1]['coordinate_status'] == 'unresolved'
    assert len(connections) == 2
    assert connections[1]['departure'] == 7 * 3600 + 40 * 60
    assert connections[1]['arrival'] == 10 * 3600 + 55 * 60
    assert connections[1]['source_row'] == 34


def test_conflicting_station_pins_are_not_silently_replaced():
    timetable, pins, regions = data()
    other = deepcopy(pins[0])
    other['latitude'] += .01
    with pytest.raises(ValueError, match='Conflicting'):
        build_rows(timetable, pins + [other], regions, 'snapshot')


def test_duplicate_trip_identity_cannot_be_published():
    timetable, pins, regions = data()
    timetable['trips'].append(deepcopy(timetable['trips'][0]))
    with pytest.raises(ValueError, match='Duplicate'):
        build_rows(timetable, pins, regions, 'snapshot')


def test_unmapped_atlas_region_is_explicitly_empty_before_storage():
    timetable, pins, regions = data()
    regions[0]['atlas_region_id'] = None
    stops, _ = build_rows(timetable, pins, regions, 'snapshot')
    assert all(stop['region_id'] == '' for stop in stops)
