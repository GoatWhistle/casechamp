import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StopTime:
    stop_id: str
    name: str
    arrival_seconds: int | None
    departure_seconds: int | None
    source_row: int
    region_code: str = ""


@dataclass(frozen=True)
class ScheduledTrip:
    id: str
    route_id: str
    direction: str
    source_file: str
    source_sheet: str
    calendar: str
    stops: list[StopTime]


class ScheduleRejected(ValueError):
    pass


def tokens(value: Any) -> list[str]:
    return [part.strip().lower() for part in str(value or '').split(';')]


def clock(value: str) -> int | None:
    if value in {'', 'нет'}:
        return None
    if not re.fullmatch(r'(?:[01]?\d|2[0-3]):[0-5]\d', value):
        raise ScheduleRejected('unsupported_clock')
    hour, minute = map(int, value.split(':'))
    return hour * 3600 + minute * 60


def calendar(row: dict, column: str, size: int) -> None:
    for suffix, expected in [('period', 'круглогодично'), (column + '_days', 'ежедневно')]:
        values = tokens(row.get('winter_' + suffix))
        if len(values) not in {1, size} or any(value != expected for value in values):
            raise ScheduleRejected('unsupported_calendar')


def normalize_direction(rows: list[dict]) -> list[ScheduledTrip]:
    rows = sorted(rows, key=lambda row: row['source_row'])
    if len(rows) < 2 or len({row['source_row'] for row in rows}) != len(rows):
        raise ScheduleRejected('ambiguous_stop_sequence')
    if any(not row['stop_registry_id'] for row in rows):
        raise ScheduleRejected('missing_stop_id')
    if any(any(value not in {'', 'нет'} for value in tokens(row.get('summer_' + field)))
           for row in rows for field in ['departure_time', 'arrival_time']):
        raise ScheduleRejected('seasonal_timetable_requires_calendar')
    count = len(tokens(rows[0].get('winter_departure_time')))
    events = []
    for position, row in enumerate(rows):
        arrival = tokens(row.get('winter_arrival_time'))
        departure = tokens(row.get('winter_departure_time'))
        if position == 0 and all(value in {'', 'нет'} for value in arrival):
            arrival = ['нет'] * count
        if position == len(rows) - 1 and all(value in {'', 'нет'} for value in departure):
            departure = ['нет'] * count
        if len(arrival) != count or len(departure) != count:
            raise ScheduleRejected('unaligned_trip_columns')
        if position > 0:
            calendar(row, 'arrival', count)
        if position < len(rows) - 1:
            calendar(row, 'departure', count)
        events.append((list(map(clock, arrival)), list(map(clock, departure))))
    trips = []
    first = rows[0]
    for index in range(count):
        previous = -1
        stops = []
        for position, (row, (arrivals, departures)) in enumerate(zip(rows, events, strict=True)):
            arrival, departure = arrivals[index], departures[index]
            if (position > 0 and arrival is None) or (position < len(rows) - 1 and departure is None):
                raise ScheduleRejected('missing_intermediate_event')
            for value in [arrival, departure]:
                if value is not None:
                    if value < previous:
                        raise ScheduleRejected('unresolved_day_offset_or_time_order')
                    previous = value
            stops.append(StopTime(row['stop_registry_id'], row['stop_name'], arrival,
                                  departure, int(row['source_row']), str(row.get('stop_region_code') or '')))
        trips.append(ScheduledTrip(
            f"{first['route_registry_id']}:{first['direction']}:{index}",
            first['route_registry_id'], first['direction'], first['source_file'],
            first['source_sheet'], 'daily_all_year', stops,
        ))
    return trips


def normalize_timetables(rows: list[dict]) -> dict:
    groups = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in ['source_file', 'source_sheet', 'route_registry_id', 'direction'])
        groups[key].append(row)
    accepted, rejected = [], []
    for key, group in sorted(groups.items()):
        try:
            accepted.extend(asdict(trip) for trip in normalize_direction(group))
        except ScheduleRejected as error:
            rejected.append({'source_file': key[0], 'source_sheet': key[1], 'route_id': key[2],
                             'direction': key[3], 'reason': str(error),
                             'source_rows': sorted(row['source_row'] for row in group)})
    return {'method': 'explicit_daily_same_day_timetable_v1', 'trips': accepted, 'rejected': rejected,
            'source_rows': len(rows), 'source_directions': len(groups),
            'coordinates_verified': False, 'operating_service_verified': False,
            'timezone_verified': False, 'source_clock_semantics': 'unverified'}
