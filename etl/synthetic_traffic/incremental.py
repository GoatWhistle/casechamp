from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite

import numpy as np
from synthetic_traffic.assignment import Assignment, costs
from synthetic_traffic.incremental_paths import PathCache, checkpoint
from synthetic_traffic.model import Network, Trip


@dataclass
class IncrementalBaseline:
    network: Network
    trips: list[Trip]
    assignment: Assignment
    paths: PathCache


def _validate(
    network: Network, trips: list[Trip], iterations: int, tolerance: float
) -> None:
    if iterations < 1 or not isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Use positive iteration and convergence limits")
    for trip in trips:
        if (
            not isfinite(trip.vehicles_per_hour)
            or trip.vehicles_per_hour <= 0
            or min(trip.origin, trip.destination) < 0
            or max(trip.origin, trip.destination) >= len(network.raw_nodes)
            or trip.origin == trip.destination
        ):
            raise ValueError("Trips need distinct valid nodes and positive finite flow")


def _assign(
    network: Network,
    trips: list[Trip],
    paths: PathCache,
    iterations: int,
    tolerance: float,
    deadline: float | None,
    check: Callable[[], None] | None = None,
) -> Assignment:
    checkpoint(deadline, check)
    paths.update(network, network.free_hours, deadline)
    flow, missing, times = paths.load(network, deadline)
    gap = 0.0
    for step in range(1, iterations + 1):
        checkpoint(deadline, check)
        hours, ratio = costs(network, flow)
        paths.update(network, hours, deadline)
        auxiliary, missing, times = paths.load(network, deadline)
        total = float(flow @ hours)
        shortest = sum(
            trip.vehicles_per_hour * t
            for trip, t in zip(trips, times, strict=True)
            if t is not None
        )
        gap = max(0.0, (total - shortest) / total) if total > 0 else 0.0
        if gap <= tolerance or step == iterations:
            break
        flow += (auxiliary - flow) / (step + 1)
    return Assignment(
        flow, hours, ratio, total, missing, gap, step, gap <= tolerance, times
    )


def prepare_incremental(
    network: Network,
    trips: list[Trip],
    iterations: int = 100,
    tolerance: float = 1e-3,
    deadline: float | None = None,
    check: Callable[[], None] | None = None,
) -> IncrementalBaseline:
    _validate(network, trips, iterations, tolerance)
    checkpoint(deadline, check)
    paths = PathCache(network, trips, network.free_hours, deadline, check)
    paths.load(network, deadline)
    assignment = _assign(
        network, trips, paths.fork(), iterations, tolerance, deadline, check
    )
    return IncrementalBaseline(network, trips, assignment, paths)


def evaluate_incremental(
    baseline: IncrementalBaseline,
    network: Network,
    iterations: int = 100,
    tolerance: float = 1e-3,
    deadline: float | None = None,
    check: Callable[[], None] | None = None,
) -> Assignment:
    _validate(network, baseline.trips, iterations, tolerance)
    if not np.array_equal(network.raw_nodes, baseline.network.raw_nodes):
        raise ValueError(
            "Incremental candidates must preserve node identities and order"
        )
    checkpoint(deadline, check)
    return _assign(
        network,
        baseline.trips,
        baseline.paths.fork(),
        iterations,
        tolerance,
        deadline,
        check,
    )
