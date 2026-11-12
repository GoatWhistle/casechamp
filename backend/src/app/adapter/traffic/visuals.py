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
    network: Network, before: Assignment, after: Assignment, way_ids: list[int], original_edges: int
) -> list[TrafficRoad]:
    count = len(network.source)
    base_flow = np.pad(before.flow, (0, count - original_edges))
    priority = np.maximum(base_flow, after.flow) + np.abs(after.flow - base_flow)
    changed = np.isin(network.way_id, way_ids) | (np.arange(count) >= original_edges)
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
                float(before.ratio[index]) if index < original_edges else None,
                float(after.ratio[index]),
                bool(changed[index]),
                bool(index >= original_edges),
            )
        )
    return result
