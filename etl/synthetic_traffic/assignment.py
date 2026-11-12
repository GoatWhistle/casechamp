from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.model import Network, Trip


@dataclass
class Assignment:
    flow: NDArray[np.float64]
    hours: NDArray[np.float64]
    ratio: NDArray[np.float64]
    vehicle_hours_per_hour: float
    unserved_vehicles_per_hour: float
    relative_gap: float
    iterations: int
    converged: bool
    od_hours: list[float | None]


def costs(
    network: Network, flow: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    combined = flow.copy()
    selected = network.shared >= 0
    if selected.any():
        _, groups = np.unique(network.shared[selected], return_inverse=True)
        combined[selected] = np.bincount(groups, weights=flow[selected])[groups]
    ratio = combined / network.capacity
    hours = network.free_hours * (1 + 0.15 * ratio**4)
    if np.any(~np.isfinite(hours)):
        raise ValueError("Traffic costs overflowed; reduce the assumed demand")
    return hours, ratio


def route_graph(
    network: Network, hours: NDArray[np.float64]
) -> tuple[csr_matrix, NDArray[np.int64]]:
    order = np.lexsort((np.arange(len(hours)), hours, network.target, network.source))
    source, target = network.source[order], network.target[order]
    keep = np.r_[True, (source[1:] != source[:-1]) | (target[1:] != target[:-1])]
    chosen = order[keep]
    graph = csr_matrix(
        (hours[chosen], (source[keep], target[keep])),
        shape=(len(network.raw_nodes), len(network.raw_nodes)),
    )
    return graph, chosen


def load_paths(
    network: Network, trips: list[Trip], hours: NDArray[np.float64]
) -> tuple[NDArray[np.float64], float, list[float | None]]:
    graph, chosen = route_graph(network, hours)
    flow = np.zeros(len(hours))
    missing = 0.0
    times: list[float | None] = [None] * len(trips)
    grouped: dict[int, list[tuple[int, Trip]]] = {}
    for index, trip in enumerate(trips):
        grouped.setdefault(trip.origin, []).append((index, trip))
    size = len(network.raw_nodes)
    keys = network.source[chosen] * size + network.target[chosen]
    for origin, entries in grouped.items():
        distances, parents = dijkstra(
            graph, directed=True, indices=origin, return_predecessors=True
        )
        pending = np.zeros(size)
        for index, trip in entries:
            if not np.isfinite(distances[trip.destination]):
                missing += trip.vehicles_per_hour
                continue
            times[index] = float(distances[trip.destination])
            pending[trip.destination] += trip.vehicles_per_hour
        nodes = np.flatnonzero(parents >= 0)
        edges = np.full(size, -1, dtype=np.int64)
        edges[nodes] = chosen[
            np.searchsorted(keys, parents[nodes].astype(np.int64) * size + nodes)
        ]
        for node in nodes[np.argsort(-distances[nodes])]:
            amount = pending[node]
            if amount > 0:
                flow[edges[node]] += amount
                pending[parents[node]] += amount
    return flow, missing, times


def assign(
    network: Network,
    trips: list[Trip],
    iterations: int = 100,
    tolerance: float = 1e-3,
    progress: Callable[[int, float], None] | None = None,
) -> Assignment:
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
    flow, missing, times = load_paths(network, trips, network.free_hours)
    gap = 0.0
    for step in range(1, iterations + 1):
        if progress is not None:
            progress(step, gap)
        hours, ratio = costs(network, flow)
        auxiliary, missing, times = load_paths(network, trips, hours)
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
