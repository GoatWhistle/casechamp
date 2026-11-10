from math import cos, radians
from uuid import uuid4

from app.adapter.road_graph.data import GraphData
from app.domain.bridge_groups import BridgePart, bridge_groups, distance_to_line_km
from app.domain.errors import InvalidQuery
from app.usecase.road_corridor import BridgeCandidate, CorridorRegion, RoadCorridor


def find_bridges(
    data: GraphData, near: str, radius_km: float, name: str
) -> list[BridgeCandidate]:
    places = data.read("corridor_places", {"query": near})
    if len(places) != 1:
        raise InvalidQuery(
            "Specify one settlement, optionally with its region after a comma: "
            + "; ".join(f"{p[1]}, {p[2]}" for p in places[:10])
        )
    place = places[0]
    center = [float(place[3]), float(place[4])]
    dy = (radius_km + 0.08) / 111.195
    dx = dy / max(0.05, cos(radians(center[1])))
    rows = data.read("bridge_parts", {
        "west": center[0] - dx, "east": center[0] + dx,
        "south": center[1] - dy, "north": center[1] + dy,
    })
    if len(rows) > 2000:
        raise InvalidQuery("Too many bridge segments; reduce radius_km. No partial selection made")
    parts = [BridgePart(
        int(r[0]), str(r[1] or ""), str(r[2] or ""), str(r[3]), float(r[4] or 0),
        int(r[5]), int(r[6]), [[float(x), float(y)] for x, y in r[7]],
    ) for r in rows if len(r[7]) >= 2]
    region_rows = data.read("region_codes", {"regions": [str(place[2])]})
    if not region_rows:
        raise InvalidQuery("Search settlement has no calculation region")
    regions = [CorridorRegion(str(r[0]), str(r[1])) for r in region_rows]
    candidates = []
    for group in bridge_groups(parts):
        if name and not any(name.casefold() in f"{p.name} {p.reference}".casefold() for p in group):
            continue
        distance = min(distance_to_line_km(center, p.coordinates) for p in group)
        if distance > radius_km:
            continue
        ways = {p.way_id: p for p in group}
        labels = sorted({p.name or p.reference for p in group if p.name or p.reference})
        corridor = RoadCorridor(
            uuid4().hex, ", ".join(labels) or "Мост без названия", str(place[1]), str(place[1]),
            sorted(ways), sum(p.length_km for p in ways.values()), distance, distance,
            regions, [p.coordinates for p in group], "osm_bridge_ways_both_directions",
        )
        candidates.append(BridgeCandidate(corridor, distance, sorted({p.reference for p in group if p.reference})))
    return sorted(candidates, key=lambda c: (c.distance_km, c.corridor.way_ids))
