from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.errors import InvalidQuery
from app.domain.transit_journey import TransitConnection


@dataclass(frozen=True)
class TimetableService:
    trip_id: str
    timezone: str
    weekdays: frozenset[int]
    starts_on: date
    ends_on: date
    connections: tuple[TransitConnection, ...]
    stop_timezones: dict[str, str] = field(default_factory=dict)


def dated_connections(
    services: list[TimetableService], first_day: date, last_day: date,
) -> list[TransitConnection]:
    if last_day < first_day:
        raise InvalidQuery('Timetable end date precedes start date')
    result = []
    for service in services:
        if not (service.timezone or service.stop_timezones) or service.ends_on < service.starts_on:
            raise InvalidQuery('Service requires an explicit timezone and valid date range')
        if not service.weekdays or not service.weekdays.issubset(range(7)):
            raise InvalidQuery('Service weekdays must use Monday=0 through Sunday=6')
        zones = {}
        for connection in service.connections:
            for stop in [connection.source, connection.target]:
                name = service.stop_timezones.get(stop, '') if service.stop_timezones else service.timezone
                if not name:
                    raise InvalidQuery('Every stop requires a confirmed timezone')
                try:
                    zones[stop] = ZoneInfo(name)
                except ZoneInfoNotFoundError as error:
                    raise InvalidQuery('Unknown service timezone') from error
        day = max(first_day, service.starts_on)
        end = min(last_day, service.ends_on)
        while day <= end:
            if day.weekday() in service.weekdays:
                identifier = f'{service.trip_id}:{day.isoformat()}'
                for connection in service.connections:
                    departure = event_timestamp(day, connection.departure, zones[connection.source])
                    arrival = event_timestamp(day, connection.arrival, zones[connection.target])
                    if arrival < departure:
                        raise InvalidQuery('Arrival precedes departure in dated service')
                    result.append(TransitConnection(identifier, connection.source, connection.target,
                                                    departure, arrival, connection.sequence))
            day += timedelta(days=1)
    return sorted(result, key=lambda row: (row.departure, row.trip_id, row.sequence))


def event_timestamp(day: date, seconds: int, timezone: ZoneInfo) -> int:
    if seconds < 0:
        raise InvalidQuery('Service time must be nonnegative')
    local = datetime.combine(day, time.min, timezone) + timedelta(seconds=seconds)
    if local.replace(fold=0).utcoffset() != local.replace(fold=1).utcoffset():
        raise InvalidQuery('Ambiguous clock change requires an explicit event offset')
    return int(local.timestamp())
