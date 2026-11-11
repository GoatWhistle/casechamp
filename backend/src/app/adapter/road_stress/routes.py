from itertools import pairwise
from typing import Any

import numpy as np

from app.adapter.road_graph.bidirectional import bidirectional_path
from app.usecase.road_stress import StressPoint, StressRoute


def trace_route(
    matrix: Any, keys: Any, lengths: Any, nodes: dict[str, Any],
    origin: StressPoint, destination: StressPoint,
) -> StressRoute:
    if min(origin.node, destination.node) < 0 or max(origin.node, destination.node) >= matrix.shape[0]:
        return StressRoute("unbound", None, None, [])
    path = bidirectional_path(matrix, origin.node, destination.node, reverse=matrix)
    if path is None:
        return StressRoute("unreachable", None, None, [])
    km = origin.snap_km + destination.snap_km
    for source, target in pairwise(path.nodes):
        key = source * matrix.shape[0] + target
        position = int(np.searchsorted(keys, key))
        if position >= len(keys) or keys[position] != key:
            raise ValueError("Route geometry mismatch")
        km += float(lengths[position])
    coordinates = [[float(nodes["lon"][n]), float(nodes["lat"][n])] for n in path.nodes]
    coordinates = [[origin.longitude, origin.latitude], *coordinates,
                   [destination.longitude, destination.latitude]]
    return StressRoute("reachable", path.hours + (origin.snap_km + destination.snap_km) / 15,
                       km, coordinates)
