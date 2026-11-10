import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

MODEL_VERSION = "hansen-planned-v1"
HALF_LIVES = (2, 4, 8)
SCHEDULED_MODES = frozenset({"air", "rail", "river", "ferry"})
TERMINAL_HOURS = {"air": 2.5, "rail": 1.0, "river": 0.5, "ferry": 0.5}


@dataclass(frozen=True, slots=True)
class DepartureCost:
    planned_hours: float
    frequency_per_week: float | None
    expected_hours: float | None


def departure_cost(
    travel_hours: float,
    mode: str,
    frequency: float | None,
    assumed: bool = False,
    terminal_hours: float | None = None,
) -> DepartureCost:
    if not math.isfinite(travel_hours) or travel_hours < 0:
        raise ValueError("Travel time must be finite and nonnegative")
    overhead = TERMINAL_HOURS.get(mode, 0.0) if terminal_hours is None else terminal_hours
    if not math.isfinite(overhead) or overhead < 0:
        raise ValueError("Terminal time must be finite and nonnegative")
    known = frequency if not assumed and frequency is not None else None
    if known is not None and (not math.isfinite(known) or known <= 0):
        raise ValueError("Frequency must be positive and finite")
    planned = travel_hours + overhead
    expected: float | None = planned
    if mode in SCHEDULED_MODES:
        expected = None if known is None else planned + 84.0 / known
    return DepartureCost(planned, known, expected)


def access_by_half_life(
    times: NDArray[np.float64],
    markets: NDArray[np.float64],
    half_life: int,
) -> NDArray[np.float64]:
    if half_life not in HALF_LIVES:
        raise ValueError("Unsupported half-life")
    if np.isnan(times).any() or (times < 0).any():
        raise ValueError("Invalid travel times")
    if not np.isfinite(markets).all() or (markets < 0).any():
        raise ValueError("Invalid market population")
    result: NDArray[np.float64] = np.exp(-np.log(2.0) / half_life * times) @ markets
    return result
