from datetime import date, datetime

import pytest

from app.domain.errors import InvalidQuery
from app.domain.transit_calendar import TimetableService, dated_connections
from app.domain.transit_journey import TransitConnection, earliest_journey


def service(timezone: str = 'Europe/Moscow') -> TimetableService:
    return TimetableService('daily', timezone, frozenset(range(7)), date(2026, 11, 13), date(2026, 11, 14),
                            (TransitConnection('daily', 'A', 'B', 19800, 31500),))


def test_missed_last_bus_waits_for_next_day_with_distinct_trip_identity() -> None:
    events = dated_connections([service()], date(2026, 11, 13), date(2026, 11, 14))
    departure = int(datetime.fromisoformat('2026-11-13T06:00:00+03:00').timestamp())
    result = earliest_journey(events, {'A': 0}, {'B': 0}, departure, departure + 36 * 3600, 300)
    assert result is not None
    assert result.arrival == int(datetime.fromisoformat('2026-11-14T08:45:00+03:00').timestamp())
    assert events[0].trip_id != events[1].trip_id
    assert result.legs[1].arrival - result.legs[1].departure == 23 * 3600 + 30 * 60


def test_weekday_and_validity_are_both_required() -> None:
    weekly = TimetableService('friday', 'Europe/Moscow', frozenset({4}), date(2026, 11, 13),
                              date(2026, 11, 14), service().connections)
    events = dated_connections([weekly], date(2026, 11, 12), date(2026, 11, 20))
    assert len(events) == 1 and events[0].trip_id.endswith('2026-11-13')


def test_unknown_timezone_does_not_default_to_moscow() -> None:
    with pytest.raises(InvalidQuery):
        dated_connections([service('')], date(2026, 11, 13), date(2026, 11, 14))
    with pytest.raises(InvalidQuery, match='Unknown service timezone'):
        dated_connections([service('Invalid/Unknown')], date(2026, 11, 13), date(2026, 11, 14))


def test_confirmed_after_midnight_offset_is_preserved() -> None:
    overnight = TimetableService('night', 'Europe/Moscow', frozenset(range(7)), date(2026, 11, 13),
                                 date(2026, 11, 13), (TransitConnection('night', 'A', 'B', 23 * 3600, 26 * 3600),))
    events = dated_connections([overnight], date(2026, 11, 13), date(2026, 11, 13))
    assert events[0].arrival - events[0].departure == 3 * 3600
    assert events[0].arrival == int(datetime.fromisoformat('2026-11-14T02:00:00+03:00').timestamp())


def test_local_stop_clocks_are_converted_before_comparing_journey_time() -> None:
    crossing = TimetableService('crossing', '', frozenset(range(7)), date(2026, 11, 13),
                                date(2026, 11, 13), (TransitConnection('crossing', 'A', 'B', 8 * 3600, 10 * 3600),),
                                {'A': 'Europe/Moscow', 'B': 'Europe/Samara'})
    events = dated_connections([crossing], date(2026, 11, 13), date(2026, 11, 13))
    assert events[0].arrival - events[0].departure == 3600
    crossing.stop_timezones.pop('B')
    with pytest.raises(InvalidQuery, match='Every stop'):
        dated_connections([crossing], date(2026, 11, 13), date(2026, 11, 13))
