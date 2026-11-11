from threading import Lock
from typing import Any
from uuid import uuid4

import numpy as np
from scipy.sparse.csgraph import connected_components

from app.adapter.road_corridor.band import band_pairs
from app.adapter.road_corridor.bridges import find_bridges
from app.adapter.road_corridor.gaps import gap_pairs
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.routing import minimum_csr
from app.domain.errors import InvalidQuery
from app.domain.road_references import lookup_keys, reference_parts, shared_reference
from app.usecase.road_corridor import BridgeCandidate, CorridorRegion, RoadCorridor
from app.usecase.road_graph import RoadChange, RoadJob

GAP_KM = 15.0
BAND_KM = 0.5
REACH_KM = 20.0
MARKET_REACH_KM = 40.0


class CorridorResolver:
    def __init__(self, roads: RoadJobs) -> None:
        self.roads = roads
        self.resolved: dict[str, RoadCorridor] = {}
        self.settlements: tuple[list[str], Any] | None = None
        self.lock = Lock()

    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor:
        data = self.roads.data
        references = {
            str(r[0])
            for r in data.read("road_reference", {"names": lookup_keys(road_name)})
            if r[0] is not None and str(r[0]).strip()
        }
        variants = shared_reference(references, road_name)
        if not variants:
            raise InvalidQuery(
                "Road reference is ambiguous or missing: " + ", ".join(sorted(references)[:8])
            )
        selected = {int(r[0]): r for r in data.read("references", {"references": variants})}
        reference = max(
            variants,
            key=lambda v: (
                sum(v in reference_parts(str(r[3] or "")) for r in selected.values()),
                v,
            ),
        )
        endpoints = []
        for query in (origin, destination):
            locations = data.read("corridor_places", {"query": query})
            if not locations:
                raise InvalidQuery("Settlement not found: " + query)
            if len(locations) != 1:
                raise InvalidQuery(
                    "Settlement is ambiguous: "
                    + query
                    + ": "
                    + ", ".join(str(p[1]) + ", " + str(p[2]) for p in locations[:8])
                )
            endpoints.append(locations[0])
        edge_rows = data.read("corridor_edges", {"ids": list(selected)})
        node_ids = sorted({int(n) for a, b, _ in edge_rows for n in (a, b)})
        node_rows = data.read("corridor_nodes", {"ids": node_ids})
        coordinates = {int(n): (float(x), float(y)) for n, x, y in node_rows}
        xy = np.array([(x, y) for _, x, y in node_rows])
        distances = []
        for point in endpoints:
            x, y = float(point[3]), float(point[4])
            distances.append(
                np.hypot((xy[:, 0] - x) * np.cos(np.radians(y)), xy[:, 1] - y) * 111.195
            )
        markets = {str(c[0]) for c in data.read("cities")}
        reach = [MARKET_REACH_KM if str(p[1]) in markets else REACH_KM for p in endpoints]
        ids = np.array([n for n, _, _ in node_rows])
        starts = np.searchsorted(ids, [a for a, _, _ in edge_rows])
        ends = np.searchsorted(ids, [b for _, b, _ in edge_rows])
        graph = minimum_csr(starts, ends, np.ones(len(starts)), len(ids))
        component_count, labels = connected_components(graph)
        pairs = [(int(a), int(b)) for a, b, _ in edge_rows]
        spans = any(
            min(distances[0][labels == c]) <= reach[0]
            and min(distances[1][labels == c]) <= reach[1]
            for c in range(component_count)
        )
        virtual: set[tuple[int, int]] = set()
        if not spans:
            gaps = gap_pairs(ids, xy, labels, pairs, GAP_KM)
            virtual = {(min(a, b), max(a, b)) for a, b in gaps}
            pairs += gaps
            joined = minimum_csr(
                np.searchsorted(ids, [a for a, _ in pairs]),
                np.searchsorted(ids, [b for _, b in pairs]),
                np.ones(len(pairs)),
                len(ids),
            )
            component_count, labels = connected_components(joined)
        corridor: set[tuple[int, int]] = set()
        attachments = []
        for component in range(component_count):
            positions = np.flatnonzero(labels == component)
            a = int(positions[np.argmin(distances[0][positions])])
            b = int(positions[np.argmin(distances[1][positions])])
            if a == b or distances[0][a] > reach[0] or distances[1][b] > reach[1]:
                continue
            corridor.update(band_pairs(ids, xy, pairs, a, b, BAND_KM))
            attachments.append((float(distances[0][a]), float(distances[1][b])))
        corridor -= virtual
        offsets = [max((pair[i] for pair in attachments), default=0.0) for i in range(2)]
        if not corridor:
            raise InvalidQuery(
                "Named-road graph has no connected corridor between the requested cities; do not substitute a viewport fragment"
            )
        way_indices = {
            int(w)
            for a, b, w in edge_rows
            if (min(int(a), int(b)), max(int(a), int(b))) in corridor
        }
        corridor_nodes = sorted({node for pair in corridor for node in pair})
        names = [str(p[2]) for p in endpoints] + self.crossed_regions(
            np.array([coordinates[n] for n in corridor_nodes])
        )
        region_rows = data.read("region_codes", {"regions": list(dict.fromkeys(names))})
        full_pairs = {
            (min(int(a), int(b)), max(int(a), int(b)))
            for a, b, w in edge_rows
            if int(w) in way_indices
        }
        result = RoadCorridor(
            uuid4().hex,
            reference,
            str(endpoints[0][1]),
            str(endpoints[1][1]),
            sorted(int(selected[w][1]) for w in way_indices),
            sum(float(selected[w][4] or 0) for w in way_indices),
            offsets[0],
            offsets[1],
            [CorridorRegion(str(i), str(name)) for i, name in sorted(region_rows)],
            [[list(coordinates[a]), list(coordinates[b])] for a, b in sorted(full_pairs)],
        )
        with self.lock:
            self.resolved[result.id] = result
        return result

    def get(self, corridor_id: str) -> RoadCorridor:
        with self.lock:
            if corridor_id not in self.resolved:
                raise InvalidQuery("Resolve the named road corridor before closing it")
            return self.resolved[corridor_id]

    def crossed_regions(self, points: Any) -> list[str]:
        if not len(points):
            return []
        if self.settlements is None:
            rows = self.roads.data.read("settlement_regions")
            self.settlements = (
                [str(r[0]) for r in rows],
                np.array([(float(r[1]), float(r[2])) for r in rows]),
            )
        names, xy = self.settlements
        sample = points[np.linspace(0, len(points) - 1, min(len(points), 400)).astype(int)]
        scale = np.cos(np.radians(sample[:, 1]))[:, None]
        counts: dict[str, int] = {}
        for start in range(0, len(sample), 50):
            block = sample[start : start + 50]
            dx = (xy[None, :, 0] - block[:, None, 0]) * scale[start : start + 50]
            dy = xy[None, :, 1] - block[:, None, 1]
            for index in np.argmin(dx * dx + dy * dy, axis=1):
                counts[names[int(index)]] = counts.get(names[int(index)], 0) + 1
        return [name for name, count in sorted(counts.items(), key=lambda c: -c[1]) if count >= 3]

    def close(self, corridor_ids: list[str]) -> list[RoadJob]:
        corridors = [self.get(key) for key in corridor_ids]
        changes = [
            RoadChange(way, 0)
            for way in sorted({way for corridor in corridors for way in corridor.way_ids})
        ]
        regions = {region.id: region for corridor in corridors for region in corridor.regions}
        return [
            self.roads.submit(region.id, region.name, "road", changes, queue=True)
            for region in regions.values()
        ]

    def bridges(self, near: str, radius_km: float, name: str) -> list[BridgeCandidate]:
        candidates = find_bridges(self.roads.data, near, radius_km, name)
        with self.lock:
            self.resolved.update({c.corridor.id: c.corridor for c in candidates})
        return candidates

    def combine_bridges(self, bridge_ids: list[str]) -> RoadCorridor:
        bridges = [self.get(key) for key in bridge_ids]
        if any(b.scope != "osm_bridge_ways_both_directions" for b in bridges):
            raise InvalidQuery("Only bridge candidates returned by find_road_bridges can be closed")
        ways = sorted({way for bridge in bridges for way in bridge.way_ids})
        lengths = self.roads.data.read("bridge_lengths", {"ids": ways})
        if {int(r[0]) for r in lengths} != set(ways):
            raise InvalidQuery("Selected bridge ways are missing from the current graph")
        regions = {region.id: region for bridge in bridges for region in bridge.regions}
        lines = {tuple(tuple(xy) for xy in line): line for b in bridges for line in b.lines}
        combined = RoadCorridor(
            uuid4().hex,
            "; ".join(dict.fromkeys(b.road_ref for b in bridges)),
            bridges[0].origin,
            bridges[-1].destination,
            ways,
            sum(float(r[1] or 0) for r in lengths),
            0,
            0,
            list(regions.values()),
            list(lines.values()),
            "combined_osm_bridge_closures_both_directions",
        )
        with self.lock:
            self.resolved[combined.id] = combined
        return combined
