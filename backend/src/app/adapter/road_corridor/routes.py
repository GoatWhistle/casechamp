from collections.abc import Callable
from itertools import pairwise
from math import isclose
from typing import Any
from uuid import uuid4

import numpy as np

from app.adapter.road_corridor.places import corridor_places
from app.adapter.road_graph.bidirectional import bidirectional_path
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.selection_geometry import selection_geometry
from app.domain.errors import InvalidQuery
from app.usecase.road_corridor import CorridorRegion, RoadCorridor, RoadRoute


def resolve_route(
    roads: RoadJobs, origin: str, destination: str, crossed_regions: Callable[[Any], list[str]]
) -> RoadRoute:
    data = roads.data
    endpoints = corridor_places(data, origin, destination)
    attachments = {
        str(point): (int(node) if node is not None else -1, float(snap or 0))
        for point, node, snap in data.read(
            "route_points", {"points": [str(p[0]) for p in endpoints]}
        )
    }
    cities = {str(row[0]): (int(row[1]), float(row[2]) * 15) for row in data.read("cities")}
    snapped = []
    for endpoint in endpoints:
        attachment = attachments.get(str(endpoint[0]), cities.get(str(endpoint[1])))
        if attachment is None or attachment[0] < 0:
            raise InvalidQuery("Settlement has no road attachment: " + str(endpoint[1]))
        snapped.append(attachment)
    roads.delta.base.prepare()
    graph = roads.delta.base.graph
    path = bidirectional_path(graph, snapped[0][0], snapped[1][0], reverse=graph)
    if path is None:
        raise InvalidQuery(
            "No connected road path between the attached settlements in this snapshot"
        )
    pairs = {(min(a, b), max(a, b)) for a, b in pairwise(path.nodes)}
    if not pairs:
        raise InvalidQuery(
            "Both settlements attach to the same road node; specify distinct endpoints"
        )
    candidates: dict[tuple[int, int], tuple[float, int]] = {}
    for a, b, way, hours in data.read("route_edges", {"ids": path.nodes}):
        key = (min(int(a), int(b)), max(int(a), int(b)))
        value = (float(hours), int(way))
        if key in pairs and value < candidates.get(key, (float("inf"), -1)):
            candidates[key] = value
    if candidates.keys() != pairs:
        raise InvalidQuery("Route geometry does not match the calculation graph")
    if not isclose(sum(h for h, _ in candidates.values()), path.hours, rel_tol=1e-7, abs_tol=1e-8):
        raise InvalidQuery("Route weights do not match the current graph; reload its cache")
    indices = sorted({way for _, way in candidates.values()})
    ways = data.read("references_by_ids", {"ids": indices})
    if {int(row[0]) for row in ways} != set(indices):
        raise InvalidQuery("Route road attributes are incomplete")
    way_ids = sorted(int(row[1]) for row in ways)
    geometry = selection_geometry(data, way_ids)
    points = np.column_stack(
        [
            data.nodes["lon"][path.nodes],
            data.nodes["lat"][path.nodes],
        ]
    )
    names = list(dict.fromkeys([str(p[2]) for p in endpoints] + crossed_regions(points)))
    regions = data.read("region_codes", {"regions": names})
    references = list(dict.fromkeys(str(row[3]) for row in ways if row[3]))
    return RoadRoute(
        RoadCorridor(
            uuid4().hex,
            "; ".join(references) or "road route",
            str(endpoints[0][1]),
            str(endpoints[1][1]),
            way_ids,
            geometry.length_km,
            snapped[0][1],
            snapped[1][1],
            [CorridorRegion(str(code), str(name)) for code, name in sorted(regions)],
            geometry.lines,
            "fastest_road_route_whole_osm_ways_both_directions",
        ),
        path.hours + sum(snap for _, snap in snapped) / 15,
    )
