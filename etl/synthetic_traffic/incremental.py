from collections.abc import Callable
from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path

import numpy as np
from synthetic_traffic.assignment import Assignment, costs
from synthetic_traffic.edge_identity import align_edges
from synthetic_traffic.incremental_paths import PathCache, checkpoint
from synthetic_traffic.initial_flow_checkpoint import feasible_initial_flow
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.origin_flows import (
    OriginFlows,
    blend_flows,
    current_flows,
    remap_flows,
)
from synthetic_traffic.origin_store import OriginStore


@dataclass
class IncrementalBaseline:
    network: Network
    trips: list[Trip]
    assignment: Assignment
    paths: PathCache
    origin_flows: OriginFlows = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


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
    initial_flow: np.ndarray | None = None,
    origin_flows: OriginFlows | None = None,
    progress: Callable[[dict], None] | None = None,
) -> Assignment:
    checkpoint(deadline, check)
    if initial_flow is None:
        paths.update(network, network.free_hours, deadline)
        flow, missing, times = paths.load(network, deadline)
    else:
        flow = initial_flow.copy()
    if origin_flows is not None and not origin_flows:
        origin_flows.update(current_flows(paths))
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
        if progress is not None:
            progress({'stage': 'assignment', 'iteration': step, 'relative_gap': gap,
                      'converged': gap <= tolerance})
        if gap <= tolerance or step == iterations:
            break
        flow += (auxiliary - flow) / (step + 1)
        if origin_flows is not None:
            blend_flows(origin_flows, current_flows(paths), 1 / (step + 1))
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
    tree_directory: Path | None = None,
    path_limit: float = np.inf,
    progress: Callable[[dict], None] | None = None,
    initial_flows: OriginFlows | None = None,
) -> IncrementalBaseline:
    _validate(network, trips, iterations, tolerance)
    checkpoint(deadline, check)
    if (isinstance(initial_flows, OriginStore) and tree_directory is not None
            and initial_flows.directory.resolve() == (tree_directory.parent / 'flows').resolve()):
        raise ValueError('Initial flow checkpoint must be separate from mutable work files')
    initial = feasible_initial_flow(network, trips, initial_flows) if initial_flows is not None else None
    hours = costs(network, initial)[0] if initial is not None else network.free_hours
    paths = PathCache(network, trips, hours, deadline, check, tree_directory, path_limit, progress,
                      replace_tree_cache=initial is not None)
    paths.load(network, deadline)
    origin_flows: OriginFlows = {} if tree_directory is None else OriginStore(tree_directory.parent / "flows", "flows")
    if initial_flows is not None:
        origin_flows.clear()
        origin_flows.update(initial_flows)
    assignment = _assign(
        network, trips, paths, iterations, tolerance, deadline, check,
        initial_flow=initial, origin_flows=origin_flows, progress=progress
    )
    paths.repaired_origins = paths.changed_nodes = 0
    return IncrementalBaseline(network, trips, assignment, paths, origin_flows)


def evaluate_incremental(
    baseline: IncrementalBaseline,
    network: Network,
    iterations: int = 100,
    tolerance: float = 1e-3,
    deadline: float | None = None,
    check: Callable[[], None] | None = None,
    progress: Callable[[dict], None] | None = None,
) -> Assignment:
    _validate(network, baseline.trips, iterations, tolerance)
    if not np.array_equal(network.raw_nodes, baseline.network.raw_nodes):
        raise ValueError(
            "Incremental candidates must preserve node identities and order"
        )
    checkpoint(deadline, check)
    same_edges = all(
        np.array_equal(getattr(network, key), getattr(baseline.network, key))
        for key in ("source", "target", "way_id")
    )
    initial_flow = baseline.assignment.flow if same_edges and baseline.assignment.converged else None
    paths = baseline.paths.fork()
    paths.check = check
    if initial_flow is None and baseline.assignment.converged and baseline.origin_flows:
        mapping = align_edges(baseline.network, network)
        hours = network.free_hours.copy()
        present = mapping >= 0
        hours[present] = baseline.assignment.hours[mapping[present]]
        del mapping, present
        paths.update(network, hours, deadline)
        paths.load(network, deadline)
        initial_flow, _ = remap_flows(baseline.network, network, baseline.origin_flows, paths)
    return _assign(
        network,
        baseline.trips,
        paths,
        iterations,
        tolerance,
        deadline,
        check,
        initial_flow,
        progress=progress,
    )
