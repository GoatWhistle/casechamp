import pytest

from app.domain.errors import InvalidQuery
from app.domain.transit_journey import TransitConnection, earliest_journey


def test_walking_waiting_and_transfer_miss_are_included() -> None:
    timetable = [TransitConnection('first', 'A', 'B', 600, 1200),
                 TransitConnection('missed', 'B', 'C', 1250, 1300),
                 TransitConnection('second', 'B', 'C', 1500, 1800)]
    result = earliest_journey(timetable, {'A': 300}, {'C': 120}, 0, 3600, 120)
    assert result is not None
    assert result.arrival == 1920 and result.transfers == 1
    assert sum(leg.arrival - leg.departure for leg in result.legs) == 1920
    assert [leg.trip_id for leg in result.legs if leg.mode == 'bus'] == ['first', 'second']
    assert sum(leg.arrival - leg.departure for leg in result.legs if leg.mode == 'wait') == 600


def test_same_bus_dwell_does_not_require_transfer_buffer() -> None:
    timetable = [TransitConnection('through', 'A', 'B', 60, 120),
                 TransitConnection('through', 'B', 'C', 150, 240, sequence=1)]
    result = earliest_journey(timetable, {'A': 0}, {'C': 0}, 0, 600, 300)
    assert result is not None and result.boardings == 1
    assert result.arrival == 240
    assert [(leg.departure, leg.arrival) for leg in result.legs if leg.mode == 'dwell'] == [(120, 150)]


def test_walking_between_platforms_preserves_transfer_requirement() -> None:
    timetable = [TransitConnection('first', 'A', 'B', 60, 120),
                 TransitConnection('too_early', 'D', 'C', 200, 240),
                 TransitConnection('second', 'D', 'C', 300, 360)]
    result = earliest_journey(timetable, {'A': 0}, {'C': 0}, 0, 600, 60, {'B': {'D': 60}})
    assert result is not None and result.arrival == 360 and result.transfers == 1


def test_later_express_beats_earlier_service_and_direction_is_preserved() -> None:
    timetable = [TransitConnection('slow', 'A', 'B', 100, 1000),
                 TransitConnection('express', 'A', 'B', 200, 500)]
    result = earliest_journey(timetable, {'A': 0}, {'B': 0}, 0, 2000, 0)
    assert result is not None and result.arrival == 500
    assert earliest_journey(timetable, {'B': 0}, {'A': 0}, 0, 2000, 0) is None
    assert earliest_journey(timetable, {'A': 0}, {'B': 0}, 201, 2000, 0) is None


def test_invalid_time_is_not_silently_routed() -> None:
    with pytest.raises(InvalidQuery):
        earliest_journey([TransitConnection('bad', 'A', 'B', 100, 50)], {'A': 0}, {'B': 0}, 0, 2000, 0)
