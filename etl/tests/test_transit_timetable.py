from copy import deepcopy

import pytest
from transit_timetable import normalize_timetables


def rows():
    result = []
    for number, (stop, arrival, departure) in enumerate([
        ('A', 'нет;нет', '05:30;07:40'), ('B', '08:45;10:55', 'нет;нет'),
    ]):
        result.append({'source_file': 'source.xlsx', 'source_sheet': 'forward',
                       'route_registry_id': '23.23.160', 'direction': 'forward',
                       'stop_registry_id': stop, 'stop_name': stop, 'source_row': number + 34,
                       'winter_arrival_time': arrival, 'winter_departure_time': departure,
                       'winter_arrival_days': 'ежедневно', 'winter_departure_days': 'ежедневно',
                       'winter_period': 'круглогодично'})
    return result


def test_preserves_column_pairing_and_missing_terminal_events():
    source = rows()
    before = deepcopy(source)
    result = normalize_timetables(source)
    assert result['rejected'] == []
    assert len(result['trips']) == 2
    for trip in result['trips']:
        start, end = trip['stops']
        assert start['arrival_seconds'] is None and end['departure_seconds'] is None
        assert end['arrival_seconds'] - start['departure_seconds'] == 195 * 60
    assert source == before
    assert result['coordinates_verified'] is False


@pytest.mark.parametrize(('column', 'value', 'reason'), [
    ('winter_arrival_days', '1 через 1', 'unsupported_calendar'),
    ('winter_arrival_time', '08:45', 'unaligned_trip_columns'),
    ('winter_arrival_time', '04:45;10:55', 'unresolved_day_offset_or_time_order'),
    ('winter_arrival_time', 'нет;10:55', 'missing_intermediate_event'),
    ('summer_arrival_time', '09:00;11:00', 'seasonal_timetable_requires_calendar'),
])
def test_ambiguous_direction_is_quarantined_without_partial_trips(column, value, reason):
    source = rows()
    source[1][column] = value
    result = normalize_timetables(source)
    assert result['trips'] == []
    assert result['rejected'][0]['reason'] == reason
    assert result['rejected'][0]['source_rows'] == [34, 35]
