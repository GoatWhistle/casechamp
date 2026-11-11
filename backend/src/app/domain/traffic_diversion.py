from dataclasses import dataclass, replace
from math import isfinite

from app.domain.errors import InvalidQuery


@dataclass(frozen=True)
class TrafficAssumptions:
    utilization: float = 0.5
    duration_hours: float = 1.0
    capacity_per_lane_pcu_h: float = 1800.0

    def validate(self) -> None:
        values = (self.utilization, self.duration_hours, self.capacity_per_lane_pcu_h)
        if any(isinstance(v, bool) or not isfinite(v) for v in values):
            raise InvalidQuery("Traffic assumptions must be finite numbers")
        if not 0 < self.utilization < 1:
            raise InvalidQuery("Background utilization must be between zero and one")
        if not 0 < self.duration_hours <= 24:
            raise InvalidQuery("Use a constant-demand closure window of up to 24 hours")
        if not 100 <= self.capacity_per_lane_pcu_h <= 3000:
            raise InvalidQuery("Capacity assumption must be between 100 and 3000 PCU/lane/hour")


@dataclass(frozen=True)
class Detour:
    free_hours: float
    capacity_pcu_h: float
    way_ids: tuple[int, ...] = ()
    assumed_lane_ways: tuple[int, ...] = ()
    segments: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class AssignedDetour:
    route: Detour
    flow_pcu_h: float
    background_pcu_h: float
    demand_capacity_ratio: float
    mean_hours: float
    queue_at_end_pcu: float
    mean_queue_hours: float


@dataclass(frozen=True)
class DiversionResult:
    assumptions: TrafficAssumptions
    source_capacity_pcu_h: float
    displaced_flow_pcu_h: float
    assigned_flow_pcu_h: float
    unserved_flow_pcu_h: float
    routes: tuple[AssignedDetour, ...]
    mean_detour_hours: float | None
    queue_at_end_pcu: float
    method: str = "edge_disjoint_detours_fluid_queue_v1"
    scope: str = "independent_pair_representative_direction_not_regional_OD"
    candidate_limit: int = 5
    source_way_ids: tuple[int, ...] = ()
    assumed_source_lane_ways: tuple[int, ...] = ()
    corridor_before_hours: float | None = None


def route_time(route: Detour, flow: float, assumptions: TrafficAssumptions) -> float:
    ratio = assumptions.utilization + flow / route.capacity_pcu_h
    moving = (
        sum(
            hours * (1 + 0.15 * min(assumptions.utilization + flow / capacity, 1) ** 4)
            for hours, capacity in route.segments
        )
        if route.segments
        else (route.free_hours * (1 + 0.15 * min(ratio, 1) ** 4))
    )
    return moving + max(ratio - 1, 0) * assumptions.duration_hours / 2


def assign_diversion(
    source_capacity: float,
    routes: list[Detour],
    assumptions: TrafficAssumptions,
) -> DiversionResult:
    assumptions.validate()
    if not isfinite(source_capacity) or source_capacity <= 0:
        raise InvalidQuery("The closed corridor needs positive capacity")
    if len(routes) > 5 or any(
        not isfinite(r.capacity_pcu_h)
        or r.capacity_pcu_h <= 0
        or not isfinite(r.free_hours)
        or r.free_hours <= 0
        for r in routes
    ):
        raise InvalidQuery("Supply up to five valid edge-disjoint detours")
    demand = source_capacity * assumptions.utilization
    if not routes:
        return DiversionResult(assumptions, source_capacity, demand, 0, demand, (), None, 0)

    def flow_at_cost(route: Detour, cost: float) -> float:
        if route_time(route, 0, assumptions) >= cost:
            return 0
        lo, hi = 0.0, demand
        for _ in range(55):
            mid = (lo + hi) / 2
            if route_time(route, mid, assumptions) < cost:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    low = min(route_time(r, 0, assumptions) for r in routes)
    high = max(route_time(r, demand, assumptions) for r in routes)
    for _ in range(60):
        cost = (low + high) / 2
        if sum(flow_at_cost(r, cost) for r in routes) < demand:
            low = cost
        else:
            high = cost
    flows = [flow_at_cost(r, high) for r in routes]
    scale = demand / sum(flows)
    assigned = []
    for route, raw_flow in zip(routes, flows, strict=True):
        flow = raw_flow * scale
        ratio = assumptions.utilization + flow / route.capacity_pcu_h
        queue = max(ratio - 1, 0) * route.capacity_pcu_h * assumptions.duration_hours
        assigned.append(
            AssignedDetour(
                replace(route, segments=()),
                flow,
                route.capacity_pcu_h * assumptions.utilization,
                ratio,
                route_time(route, flow, assumptions),
                queue,
                max(ratio - 1, 0) * assumptions.duration_hours / 2,
            )
        )
    return DiversionResult(
        assumptions,
        source_capacity,
        demand,
        sum(r.flow_pcu_h for r in assigned),
        0,
        tuple(assigned),
        sum(r.mean_hours * r.flow_pcu_h for r in assigned) / demand,
        sum(r.queue_at_end_pcu for r in assigned),
    )
