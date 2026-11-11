from dataclasses import dataclass
from itertools import pairwise
from math import isclose
from typing import Any

from app.adapter.road_graph.bidirectional import RoadPath
from app.adapter.road_graph.data import GraphData
from app.domain.errors import InvalidQuery
from app.domain.road_cost import evaluate_road
from app.domain.traffic_diversion import Detour, TrafficAssumptions


@dataclass(frozen=True)
class TrafficEdge:
    a: int
    b: int
    way_id: int
    free_hours: float
    capacity: float
    assumed_lanes: bool


class TrafficPaths:
    def __init__(self, data: GraphData, assumptions: TrafficAssumptions) -> None:
        self.data, self.assumptions = data, assumptions
        self.profiles: dict[int, dict[str, Any]] = {}

    def edges(self, path: RoadPath, excluded: set[int]) -> list[TrafficEdge]:
        pairs = {(min(a, b), max(a, b)) for a, b in pairwise(path.nodes)}
        candidates: dict[tuple[int, int], tuple[float, int]] = {}
        for a, b, way, hours in self.data.read("route_edges", {"ids": path.nodes}):
            key = (min(int(a), int(b)), max(int(a), int(b)))
            value = (float(hours), int(way))
            if (
                key in pairs
                and int(way) not in excluded
                and value < candidates.get(key, (float("inf"), -1))
            ):
                candidates[key] = value
        if candidates.keys() != pairs or not isclose(
            sum(h for h, _ in candidates.values()),
            path.hours,
            rel_tol=1e-6,
            abs_tol=1e-8,
        ):
            raise InvalidQuery("Traffic route attributes do not match the road graph")
        indices = sorted({index for _, index in candidates.values()})
        ways = {int(r[0]): int(r[1]) for r in self.data.read("references_by_ids", {"ids": indices})}
        if ways.keys() != set(indices):
            raise InvalidQuery("Traffic route is missing road identifiers")
        missing = [way for way in ways.values() if way not in self.profiles]
        self.profiles.update(
            {
                ways[index]: profile
                for index, profile in self.data.cost_profiles(missing).items()
                if index in ways
            }
        )
        result = []
        for a, b in pairwise(path.nodes):
            hours, index = candidates[min(a, b), max(a, b)]
            way = ways[index]
            profile = self.profiles.get(way)
            if profile is None:
                raise InvalidQuery("Road capacity profiles are unavailable for this route")
            try:
                cost = evaluate_road(length_km=1, **profile)
            except ValueError as error:
                raise InvalidQuery("Unresolved road capacity: " + str(error)) from error
            if cost.capacity_pcu_h is None or cost.effective_lanes is None:
                raise InvalidQuery(
                    "Traffic diversion requires resolved road lanes; ferries are unsupported"
                )
            result.append(
                TrafficEdge(
                    a,
                    b,
                    way,
                    hours * cost.free_flow_hours / cost.travel_hours,
                    cost.effective_lanes * self.assumptions.capacity_per_lane_pcu_h,
                    "unknown" in cost.lane_basis or "partial" in cost.lane_basis,
                )
            )
        return result


def detour(edges: list[TrafficEdge]) -> Detour:
    return Detour(
        sum(e.free_hours for e in edges),
        min(e.capacity for e in edges),
        tuple(sorted({e.way_id for e in edges})),
        tuple(sorted({e.way_id for e in edges if e.assumed_lanes})),
        tuple((e.free_hours, e.capacity) for e in edges),
    )


def remove_path(matrix: Any, nodes: list[int]) -> None:
    for a, b in pairwise(nodes):
        for source, target in ((a, b), (b, a)):
            start, end = matrix.indptr[source : source + 2]
            positions = matrix.indices[start:end] == target
            matrix.data[start:end][positions] = float("inf")
