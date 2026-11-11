from dataclasses import dataclass, replace
from typing import Any

from app.adapter.road_corridor.traffic_paths import TrafficEdge, TrafficPaths, detour, remove_path
from app.adapter.road_graph.bidirectional import bidirectional_path
from app.domain.connectivity import PairAccess
from app.domain.traffic_diversion import DiversionResult, TrafficAssumptions, assign_diversion


@dataclass(frozen=True)
class LoadedPair:
    before: PairAccess
    after: PairAccess
    traffic: DiversionResult | None
    time_loss_pcu_hours: float | None


def apply_detour_load(
    matrix: Any,
    edges: list[TrafficEdge],
    flow: float,
    queue_hours: float,
    assumptions: TrafficAssumptions,
) -> None:
    bottleneck = min(range(len(edges)), key=lambda i: edges[i].capacity)
    for index, edge in enumerate(edges):
        ratio = assumptions.utilization + flow / edge.capacity
        hours = edge.free_hours * (1 + 0.15 * min(ratio, 1) ** 4)
        if index == bottleneck:
            hours += queue_hours
        for source, target in ((edge.a, edge.b), (edge.b, edge.a)):
            start, end = matrix.indptr[source : source + 2]
            positions = matrix.indices[start:end] == target
            matrix.data[start:end][positions] = hours


def loaded_pair(
    profiles: TrafficPaths,
    baseline: Any,
    changed: Any,
    origin: tuple[int, float],
    destination: tuple[int, float],
    closed_ways: set[int],
    excluded_indices: set[int],
    assumptions: TrafficAssumptions,
) -> LoadedPair | None:
    if min(origin[0], destination[0]) < 0:
        return None
    initial = bidirectional_path(baseline, origin[0], destination[0], reverse=baseline)
    if initial is None or not initial.nodes or len(initial.nodes) == 1:
        return None
    original = profiles.edges(initial, set())
    background_factor = 1 + 0.15 * assumptions.utilization**4
    attachment = (origin[1] + destination[1]) / 15
    before_hours = sum(e.free_hours for e in original) * background_factor + attachment
    before = PairAccess("reachable", before_hours)
    affected = [i for i, e in enumerate(original) if e.way_id in closed_ways]
    if not affected:
        return LoadedPair(before, before, None, 0)
    first, last = min(affected), max(affected) + 1
    while (
        first > 0
        and baseline.indptr[initial.nodes[first] + 1] - baseline.indptr[initial.nodes[first]] <= 2
    ):
        first -= 1
    while (
        last < len(initial.nodes) - 1
        and baseline.indptr[initial.nodes[last] + 1] - baseline.indptr[initial.nodes[last]] <= 2
    ):
        last += 1
    candidates = changed.copy()
    route_edges = []
    for _ in range(5):
        route = bidirectional_path(
            candidates, initial.nodes[first], initial.nodes[last], reverse=candidates
        )
        if route is None:
            break
        route_edges.append(profiles.edges(route, excluded_indices))
        remove_path(candidates, route.nodes)
    source_capacity = min(original[i].capacity for i in affected)
    span_before = sum(e.free_hours for e in original[first:last]) * background_factor
    result = replace(
        assign_diversion(source_capacity, [detour(e) for e in route_edges], assumptions),
        source_way_ids=tuple(sorted({original[i].way_id for i in affected})),
        assumed_source_lane_ways=tuple(
            sorted({original[i].way_id for i in affected if original[i].assumed_lanes})
        ),
        corridor_before_hours=span_before,
    )
    loaded = changed.copy()
    loaded.data *= background_factor
    for edges, assigned in zip(route_edges, result.routes, strict=True):
        apply_detour_load(
            loaded, edges, assigned.flow_pcu_h, assigned.mean_queue_hours, assumptions
        )
    final = bidirectional_path(loaded, origin[0], destination[0], reverse=loaded)
    after = (
        PairAccess("reachable", final.hours + attachment)
        if final
        else PairAccess("unreachable", None)
    )
    loss = (
        None
        if result.mean_detour_hours is None
        else (
            (result.mean_detour_hours - span_before)
            * result.displaced_flow_pcu_h
            * assumptions.duration_hours
        )
    )
    return LoadedPair(before, after, result, loss)
