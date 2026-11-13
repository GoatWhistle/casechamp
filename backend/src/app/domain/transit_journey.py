from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Literal

from app.domain.errors import InvalidQuery


@dataclass(frozen=True)
class TransitConnection:
    trip_id: str
    source: str
    target: str
    departure: int
    arrival: int
    sequence: int = 0


@dataclass(frozen=True)
class JourneyLeg:
    mode: Literal['walk', 'wait', 'dwell', 'bus']
    source: str
    target: str
    departure: int
    arrival: int
    trip_id: str | None = None


@dataclass(frozen=True)
class TransitJourney:
    departure: int
    arrival: int
    boardings: int
    legs: tuple[JourneyLeg, ...]

    @property
    def transfers(self) -> int:
        return max(0, self.boardings - 1)


State = tuple[str, str | None, bool, int]


def earliest_journey(
    connections: list[TransitConnection], access: dict[str, int], egress: dict[str, int],
    departure: int, horizon: int, transfer_seconds: int,
    walking_transfers: dict[str, dict[str, int]] | None = None,
) -> TransitJourney | None:
    if departure < 0 or horizon <= departure or transfer_seconds < 0:
        raise InvalidQuery('Use nonnegative departure/transfer times and a later horizon')
    walking = walking_transfers or {}
    durations = [*access.values(), *egress.values(),
                 *(value for targets in walking.values() for value in targets.values())]
    if any(value < 0 for value in durations):
        raise InvalidQuery('Walking durations must be nonnegative')
    outgoing: dict[str, list[TransitConnection]] = defaultdict(list)
    for connection in connections:
        if not connection.trip_id or connection.departure < 0 or connection.arrival < connection.departure:
            raise InvalidQuery('Timetable contains an invalid connection')
        outgoing[connection.source].append(connection)
    departures = {}
    for stop, values in outgoing.items():
        values.sort(key=lambda row: row.departure)
        departures[stop] = [row.departure for row in values]
    sequence = count()
    heap: list[tuple[int, int, State, int, tuple[JourneyLeg, ...]]] = []
    best: dict[State, tuple[int, int]] = {}

    def offer(time: int, state: State, boardings: int, legs: tuple[JourneyLeg, ...]) -> None:
        if time > horizon or (time, boardings) >= best.get(state, (horizon + 1, 0)):
            return
        best[state] = (time, boardings)
        heappush(heap, (time, next(sequence), state, boardings, legs))

    for stop, seconds in access.items():
        offer(departure + seconds, (stop, None, False, -1), 0,
              (JourneyLeg('walk', 'origin', stop, departure, departure + seconds),))
    result: TransitJourney | None = None
    while heap:
        time, _, state, boardings, legs = heappop(heap)
        if best[state] != (time, boardings):
            continue
        if result is not None and time > result.arrival:
            break
        stop, previous_trip, boarded, previous_sequence = state
        if stop in egress and time + egress[stop] <= horizon:
            candidate = TransitJourney(departure, time + egress[stop], boardings,
                                       legs + (JourneyLeg('walk', stop, 'destination', time, time + egress[stop]),))
            if result is None or (candidate.arrival, candidate.boardings) < (result.arrival, result.boardings):
                result = candidate
        for target, seconds in walking.get(stop, {}).items():
            offer(time + seconds, (target, None, boarded, -1), boardings,
                  legs + (JourneyLeg('walk', stop, target, time, time + seconds),))
        options = outgoing.get(stop, [])
        for connection in options[bisect_left(departures.get(stop, []), time):]:
            same_trip = previous_trip == connection.trip_id and connection.sequence == previous_sequence + 1
            ready = time + (transfer_seconds if boarded and not same_trip else 0)
            if connection.departure < ready or connection.arrival > horizon:
                continue
            prefix = legs
            if connection.departure > time:
                prefix += (JourneyLeg('dwell' if same_trip else 'wait', stop, stop,
                                      time, connection.departure, connection.trip_id if same_trip else None),)
            offer(connection.arrival, (connection.target, connection.trip_id, True, connection.sequence),
                  boardings + (0 if same_trip else 1), prefix + (JourneyLeg(
                      'bus', stop, connection.target, connection.departure, connection.arrival, connection.trip_id),))
    return result
