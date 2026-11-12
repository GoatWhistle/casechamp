from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

import numpy as np
from synthetic_traffic.assignment import Assignment, route_graph
from synthetic_traffic.incremental_paths import PathCache
from synthetic_traffic.model import Network, Trip


def _known_unserved(value: object) -> bool:
    return (
        isinstance(value, (int, float, np.floating)) and isfinite(value) and value >= 0
    )


def _bounds(bounds: Sequence[float] | None) -> np.ndarray | None:
    if bounds is None:
        return None
    value = np.asarray(bounds, dtype=float)
    if value.shape != (4,) or not np.isfinite(value).all():
        raise ValueError("Focus bounds require four finite coordinates")
    west, south, east, north = value
    if (
        west >= east
        or south >= north
        or west < -180
        or east > 180
        or south < -90
        or north > 90
    ):
        raise ValueError("Focus bounds must be an ordered geographic rectangle")
    return value


def _inside(network: Network, bounds: np.ndarray) -> np.ndarray:
    west, south, east, north = bounds
    return (
        (network.lon >= west)
        & (network.lon <= east)
        & (network.lat >= south)
        & (network.lat <= north)
    )


def _focused_edges(network: Network, bounds: np.ndarray | None) -> np.ndarray:
    if bounds is None:
        return np.ones(len(network.source), dtype=bool)
    x, y = network.lon[network.source], network.lat[network.source]
    dx = network.lon[network.target] - x
    dy = network.lat[network.target] - y
    selected = _segments(x, y, dx, dy, bounds)
    for way, coordinates in (network.geometries or {}).items():
        points = np.asarray(coordinates, dtype=float)
        starts, vectors = points[:-1], np.diff(points, axis=0)
        selected[network.way_id == way] = bool(
            _segments(
                starts[:, 0], starts[:, 1], vectors[:, 0], vectors[:, 1], bounds
            ).any()
        )
    return selected


def _segments(x, y, dx, dy, bounds):
    west, south, east, north = bounds
    low, high = np.zeros(len(x)), np.ones(len(x))
    valid = np.ones(len(x), dtype=bool)
    for p, q in ((-dx, x - west), (dx, east - x), (-dy, y - south), (dy, north - y)):
        zero = p == 0
        valid &= ~zero | (q >= 0)
        ratio = np.divide(q, p, out=np.zeros_like(q), where=~zero)
        low = np.where(p < 0, np.maximum(low, ratio), low)
        high = np.where(p > 0, np.minimum(high, ratio), high)
    return valid & (low <= high)


def _transit(
    network: Network, baseline: Assignment, trips: list[Trip], bounds: np.ndarray
) -> np.ndarray:
    cache = PathCache(network, trips, baseline.hours)
    _, chosen = route_graph(network, baseline.hours)
    focused = _focused_edges(network, bounds)
    crossing_pairs = {
        (int(network.source[e]), int(network.target[e])) for e in chosen if focused[e]
    }
    inside = _inside(network, bounds)
    selected = np.zeros(len(trips), dtype=bool)
    for origin, entries in cache.entries.items():
        if inside[origin]:
            continue
        tree = cache.trees[origin]
        crossing = np.zeros(len(network.raw_nodes), dtype=bool)
        nodes = np.flatnonzero(tree.parent >= 0)
        for node in nodes[np.argsort(tree.distance[nodes])]:
            parent = int(tree.parent[node])
            crossing[node] = crossing[parent] or (parent, int(node)) in crossing_pairs
        for index, trip in entries:
            selected[index] = (
                not inside[trip.destination] and crossing[trip.destination]
            )
    return selected


@dataclass
class ObjectiveScorer:
    objective: str
    baseline: Assignment
    trips: list[Trip]
    bounds: np.ndarray | None
    selected: np.ndarray

    def _eligible(self, result: Assignment) -> bool:
        if not result.converged or len(result.od_hours) != len(self.trips):
            return False
        if (
            not _known_unserved(result.unserved_vehicles_per_hour)
            or result.unserved_vehicles_per_hour
            > self.baseline.unserved_vehicles_per_hour + 1e-9
        ):
            return False
        for before, after in zip(self.baseline.od_hours, result.od_hours, strict=True):
            if before is not None and (
                after is None or not isfinite(after) or after < 0
            ):
                return False
        return True

    def metrics(self, network: Network, result: Assignment) -> dict[str, object]:
        eligible = self._eligible(result)
        value: float | None = None
        if eligible and self.objective == "congestion":
            if len(result.flow) != len(network.source) or len(result.hours) != len(
                network.source
            ):
                eligible = False
            else:
                selected = _focused_edges(network, self.bounds)
                delay = result.flow * np.maximum(0, result.hours - network.free_hours)
                eligible = bool(
                    np.isfinite(delay).all()
                    and np.all(result.flow >= 0)
                    and np.all(result.hours > 0)
                )
                if eligible:
                    value = float(delay[selected].sum())
        elif eligible:
            entries = [
                (trip.vehicles_per_hour, time)
                for trip, time, chosen in zip(
                    self.trips, result.od_hours, self.selected, strict=True
                )
                if chosen
            ]
            if any(
                time is None or not isfinite(time) or time < 0 for _, time in entries
            ):
                eligible = False
            else:
                value = sum(flow * float(time) for flow, time in entries) / sum(
                    flow for flow, _ in entries
                )
        return {
            "objective": self.objective,
            "eligible": eligible,
            "score": -value if eligible and value is not None else None,
            "focused_delay_vehicle_hours_per_hour": value
            if self.objective == "congestion"
            else None,
            "transit_mean_minutes": value * 60
            if self.objective == "transit" and value is not None
            else None,
            "selected_od_pairs": int(self.selected.sum()),
            "selected_vehicles_per_hour": sum(
                t.vehicles_per_hour
                for t, chosen in zip(self.trips, self.selected, strict=True)
                if chosen
            ),
        }

    def __call__(self, network: Network, result: Assignment) -> float:
        value = self.metrics(network, result)["score"]
        return float(value) if isinstance(value, (int, float)) else -float("inf")


def build_objective(
    objective: str,
    network: Network,
    baseline: Assignment,
    trips: list[Trip],
    focus_bounds: Sequence[float] | None = None,
    transit_mask: Sequence[bool] | None = None,
) -> ObjectiveScorer:
    if objective not in {"transit", "congestion"}:
        raise ValueError(
            "Use transit or congestion here; connectivity requires the national index scorer"
        )
    if not baseline.converged or not _known_unserved(
        baseline.unserved_vehicles_per_hour
    ):
        raise ValueError(
            "Objective scoring requires a converged baseline with known unserved demand"
        )
    if len(baseline.od_hours) != len(trips) or len(baseline.hours) != len(
        network.source
    ):
        raise ValueError("Baseline assignment must align with network and trips")
    if not trips or any(
        not isfinite(t.vehicles_per_hour) or t.vehicles_per_hour <= 0 for t in trips
    ):
        raise ValueError("Objective scoring requires positive finite OD demand")
    bounds = _bounds(focus_bounds)
    selected = np.ones(len(trips), dtype=bool)
    if objective == "transit":
        if transit_mask is not None:
            selected = np.asarray(transit_mask)
            if selected.dtype != np.bool_ or selected.shape != (len(trips),):
                raise ValueError(
                    "Transit selection must be a boolean mask aligned with trips"
                )
        elif bounds is None:
            raise ValueError("Automatic transit selection requires focus bounds")
        else:
            selected = _transit(network, baseline, trips, bounds)
        if not selected.any() or any(
            t is None or not isfinite(t)
            for t, chosen in zip(baseline.od_hours, selected, strict=True)
            if chosen
        ):
            raise ValueError("No reachable baseline transit OD pairs match the focus")
    return ObjectiveScorer(objective, baseline, trips, bounds, selected)
