from math import cos, radians
from uuid import uuid4

import numpy as np
from scipy.sparse.csgraph import connected_components

from app.adapter.road_corridor.places import corridor_places
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.selection_geometry import selection_geometry
from app.adapter.road_graph.weighted import minimum_csr
from app.domain.errors import InvalidQuery
from app.usecase.road_corridor import CorridorRegion, RoadCorridor


def resolve_street(data: GraphData, name: str, place: str) -> RoadCorridor:
    point = corridor_places(data, place, place)[0]
    longitude, latitude = float(point[3]), float(point[4])
    dy = 5 / 111.195
    dx = dy / max(0.1, cos(radians(latitude)))
    rows = data.read(
        "local_road_ways",
        {
            "street": " ".join(name.casefold().replace("ё", "е").split()),
            "west": longitude - dx,
            "east": longitude + dx,
            "south": latitude - dy,
            "north": latitude + dy,
        },
    )
    if not rows:
        raise InvalidQuery("Named street not found within 5 km of settlement: " + name)
    indices = [int(row[0]) for row in rows]
    edges = data.read("corridor_edges", {"ids": indices})
    nodes = np.unique([node for a, b, _ in edges for node in (a, b)])
    if not len(nodes):
        raise InvalidQuery("Named street has no routing geometry")
    src = np.searchsorted(nodes, [a for a, _, _ in edges])
    dst = np.searchsorted(nodes, [b for _, b, _ in edges])
    count, _ = connected_components(minimum_csr(src, dst, np.ones(len(src)), len(nodes)))
    if count != 1:
        raise InvalidQuery("Several disconnected sections match the street; specify its section")
    ids = [int(row[1]) for row in rows]
    geometry = selection_geometry(data, ids)
    regions = data.read("region_codes", {"regions": [str(point[2])]})
    if not regions:
        raise InvalidQuery("Settlement region is missing from the atlas")
    return RoadCorridor(
        uuid4().hex,
        str(rows[0][2]),
        str(point[1]),
        str(point[1]),
        ids,
        geometry.length_km,
        0,
        0,
        [CorridorRegion(str(code), str(region)) for code, region in regions],
        geometry.lines,
        "connected_named_street_within_5km_of_settlement",
    )
