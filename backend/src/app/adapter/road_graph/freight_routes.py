from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.search_cache import changed_weights
from app.domain.appraisal_inputs import FreightFlow
from app.domain.errors import InvalidQuery
from app.usecase.road_profile_validation import has_profile
from app.usecase.road_records import RoadChange


def road_matrix(
    edges: dict[str, Any], weights: Any, allowed: Any, count: int
) -> tuple[Any, Any, Any]:
    finite = np.isfinite(weights) & allowed
    src = np.concatenate([edges["src"][finite], edges["dst"][finite]]).astype(np.int64)
    dst = np.concatenate([edges["dst"][finite], edges["src"][finite]]).astype(np.int64)
    hours = np.tile(weights[finite], 2).astype(np.float64)
    km = np.tile(edges["km"][finite], 2).astype(np.float64)
    keys = src * count + dst
    order = np.lexsort((km, hours, keys))
    keys = keys[order]
    starts = (
        np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]]) if len(keys) else np.array([], dtype=int)
    )
    selected = order[starts]
    keys = keys[starts]
    matrix = csr_matrix((hours[selected], (keys // count, keys % count)), shape=(count, count))
    return matrix, keys, km[selected]


def route_km(
    predecessors: Any, keys: Any, lengths: Any, source: int, target: int, count: int
) -> float:
    value = 0.0
    node = target
    for _ in range(count):
        if node == source:
            return value
        parent = int(predecessors[node])
        if parent < 0:
            raise InvalidQuery("Freight route predecessor is unavailable")
        key = parent * count + node
        position = int(np.searchsorted(keys, key))
        if position >= len(keys) or int(keys[position]) != key:
            raise InvalidQuery("Freight route mileage does not match its selected path")
        value += float(lengths[position])
        node = parent
    raise InvalidQuery("Freight route predecessor cycle")


def freight_routes(
    data: GraphData,
    region: str,
    scenario: str,
    changes: list[RoadChange],
    flows: Sequence[FreightFlow],
) -> dict[str, tuple[float, float] | None]:
    routed = [flow for flow in flows if flow.origin_point_id]
    if not routed:
        return {}
    data.load()
    points = {str(p[0]): (int(p[1]), float(p[2])) for p in data.read("points")}
    markets = {str(c[0]): (int(c[1]), float(c[2])) for c in data.read("cities")}
    origins = {str(row[0]) for row in data.read("origins", {"region": region, "season": scenario})}
    for flow in routed:
        if flow.origin_point_id not in origins or flow.market_city not in markets:
            raise InvalidQuery(
                "Freight OD must use an origin in the selected region and a known market"
            )
    ids = [change.way_id for change in changes]
    profiles = data.cost_profiles(ids) if any(has_profile(change) for change in changes) else None
    weights, _ = changed_weights(
        data.edges, data.indices_for(ids) if ids else {}, changes, profiles
    )
    count = len(data.nodes["lat"])
    matrix, keys, lengths = road_matrix(data.edges, weights, data.allowed_edges(scenario), count)
    result: dict[str, tuple[float, float] | None] = {flow.name: None for flow in routed}
    for source in sorted(
        {points[flow.origin_point_id][0] for flow in routed if flow.origin_point_id in points}
    ):
        if not 0 <= source < count:
            continue
        times, predecessors = dijkstra(
            matrix, directed=True, indices=source, return_predecessors=True
        )
        for flow in routed:
            origin = points.get(flow.origin_point_id)
            target, target_snap_h = markets[flow.market_city]
            if (
                origin is None
                or origin[0] != source
                or not 0 <= target < count
                or not np.isfinite(times[target])
            ):
                continue
            mileage = route_km(predecessors, keys, lengths, source, target, count)
            result[flow.name] = (
                float(times[target]) + origin[1] / 15 + target_snap_h,
                mileage + origin[1] + target_snap_h * 15,
            )
    return result
