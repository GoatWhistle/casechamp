import numpy as np
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.model import Network

from app.usecase.traffic import TrafficMetrics, TrafficRoad


def metrics(result: Assignment) -> TrafficMetrics:
    return TrafficMetrics(
        result.vehicle_hours_per_hour,
        result.unserved_vehicles_per_hour,
        int((result.ratio > 1).sum()),
        result.relative_gap,
        result.converged,
    )


def roads(
    network: Network,
    before: Assignment,
    after: Assignment,
    way_ids: list[int],
    original_edges: int,
    original: Network | None = None,
) -> list[TrafficRoad]:
    count = len(network.source)
    if original is None:
        base_flow = np.pad(before.flow, (0, count - original_edges))
        base_ratio = np.pad(before.ratio, (0, count - original_edges))
        new_edges = np.arange(count) >= original_edges
    else:
        lookup = {
            (int(a), int(b), int(w)): i
            for i, (a, b, w) in enumerate(
                zip(original.source, original.target, original.way_id, strict=True)
            )
        }
        positions = np.array(
            [
                lookup.get((int(a), int(b), int(w)), -1)
                for a, b, w in zip(network.source, network.target, network.way_id, strict=True)
            ]
        )
        new_edges = positions < 0
        base_flow = np.where(new_edges, 0, before.flow[np.maximum(positions, 0)])
        base_ratio = np.where(new_edges, 0, before.ratio[np.maximum(positions, 0)])
    priority = np.maximum(base_flow, after.flow) + np.abs(after.flow - base_flow)
    changed = np.isin(network.way_id, way_ids) | new_edges
    selected = np.unique(np.r_[np.argsort(-priority)[:800], np.flatnonzero(changed)])
    result = []
    for index in selected:
        if priority[index] <= 0 and not changed[index]:
            continue
        a, b = network.source[index], network.target[index]
        result.append(
            TrafficRoad(
                int(network.way_id[index]),
                [
                    [float(network.lon[a]), float(network.lat[a])],
                    [float(network.lon[b]), float(network.lat[b])],
                ],
                float(base_flow[index]),
                float(after.flow[index]),
                float(base_ratio[index]) if not new_edges[index] else None,
                float(after.ratio[index]),
                bool(changed[index]),
                bool(new_edges[index]),
            )
        )
    return result
