from dataclasses import replace
from itertools import combinations
from math import isfinite
from typing import Any

import numpy as np

from app.adapter.road_corridor.places import corridor_places
from app.adapter.road_corridor.traffic import loaded_pair
from app.adapter.road_corridor.traffic_paths import TrafficPaths
from app.adapter.road_graph.bidirectional import bidirectional_path
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.routing import minimum_csr
from app.adapter.road_graph.search_cache import changed_weights
from app.domain.connectivity import PairAccess
from app.domain.errors import InvalidQuery
from app.domain.traffic_diversion import TrafficAssumptions
from app.usecase.connectivity import (
    ConnectivityMode,
    ConnectivityPlace,
    ConnectivityResult,
    connectivity_pair,
    connectivity_result,
)
from app.usecase.road_records import RoadChange


def access(matrix: Any, origin: tuple[int, float], target: tuple[int, float]) -> PairAccess:
    if any(
        node < 0 or node >= matrix.shape[0] or not isfinite(snap) or snap < 0
        for node, snap in (origin, target)
    ):
        return PairAccess("unbound", None)
    route = bidirectional_path(matrix, origin[0], target[0], reverse=matrix)
    if route is None:
        return PairAccess("unreachable", None)
    return PairAccess("reachable", route.hours + (origin[1] + target[1]) / 15)


def calculate_connectivity(
    roads: RoadJobs,
    queries: list[str],
    mode: ConnectivityMode,
    center: str | None,
    closed_way_ids: list[int],
    traffic: TrafficAssumptions | None = None,
) -> ConnectivityResult:
    if traffic is not None:
        traffic.validate()
    data = roads.data
    endpoints = [corridor_places(data, query, query)[0] for query in queries]
    places = [ConnectivityPlace(str(p[0]), str(p[1]), str(p[2])) for p in endpoints]
    if len({p.id for p in places}) != len(places):
        raise InvalidQuery("Different names resolve to the same settlement")
    attachments = {
        str(point): (
            int(node) if node is not None else -1,
            float(snap) if snap is not None else float("nan"),
        )
        for point, node, snap in data.read("route_points", {"points": [p.id for p in places]})
    }
    snapped = [attachments.get(p.id, (-1, 0.0)) for p in places]
    roads.delta.base.prepare()
    baseline = roads.delta.base.graph
    data.attachment_audit.validate(closed_way_ids)
    changed = baseline
    indices: dict[int, int] = {}
    if closed_way_ids:
        indices = data.indices_for(closed_way_ids)
        weights, _ = changed_weights(
            data.edges, indices, [RoadChange(way, 0) for way in closed_way_ids]
        )
        allowed = data.allowed_edges("road") & np.isfinite(weights)
        changed = minimum_csr(
            data.edges["src"][allowed],
            data.edges["dst"][allowed],
            weights[allowed],
            baseline.shape[0],
        )
    center_index = queries.index(center) if center is not None else None
    selected = (
        list(combinations(range(len(places)), 2))
        if center_index is None
        else [(index, center_index) for index in range(len(places)) if index != center_index]
    )
    pairs = []
    profiles = TrafficPaths(data, traffic) if traffic else None
    for origin, destination in selected:
        before = access(baseline, snapped[origin], snapped[destination])
        after = access(changed, snapped[origin], snapped[destination]) if closed_way_ids else before
        pair = connectivity_pair(places[origin], places[destination], before, after)
        if traffic and profiles and before.status == "reachable":
            loaded = loaded_pair(
                profiles,
                baseline,
                changed,
                snapped[origin],
                snapped[destination],
                set(closed_way_ids),
                set(indices.values()),
                traffic,
            )
            if loaded is not None:
                pair = replace(
                    connectivity_pair(
                        places[origin], places[destination], loaded.before, loaded.after
                    ),
                    traffic=loaded.traffic,
                    time_loss_pcu_hours=loaded.time_loss_pcu_hours,
                )
        pairs.append(pair)
    result = connectivity_result(
        places,
        mode,
        places[center_index].id if center_index is not None else None,
        pairs,
        closed_way_ids,
        data.version,
    )
    return replace(
        result,
        traffic_assumptions=traffic,
        model_version="selected-settlements-diversion-v1" if traffic else result.model_version,
    )
