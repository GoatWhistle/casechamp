from dataclasses import replace
from threading import Lock
from typing import Any

import numpy as np
from scipy.sparse.csgraph import dijkstra

from app.adapter.normative.nearest_targets import nearest_targets
from app.adapter.normative.path_geometry import geometry, predecessor_path
from app.adapter.normative.road_closure_matrix import road_closure_matrix
from app.adapter.road_graph.delta_base import DeltaBase
from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import AccessRow, AccessState, Facility, Origin
from app.usecase.normative.route import RouteGeometry


class GraphNormativeRouting:
    def __init__(self, base: DeltaBase, approach_speed_kmh: float = 15) -> None:
        self.base = base
        self.approach_speed_kmh = approach_speed_kmh
        self.lock = Lock()
        self.cached: dict[tuple[object, ...], list[AccessRow]] = {}
        self.attachment_index: tuple[Any, Any] | None = None

    @property
    def revision(self) -> str:
        return self.base.data.revision

    def evaluate(
        self,
        origins: list[Origin],
        facilities: list[Facility],
        threshold: float,
        closed_way_ids: list[int],
    ) -> list[AccessRow]:
        with self.lock:
            return self._evaluate(origins, facilities, threshold, closed_way_ids)

    def _evaluate(
        self,
        origins: list[Origin],
        facilities: list[Facility],
        threshold: float,
        closed_way_ids: list[int],
    ) -> list[AccessRow]:
        key = (tuple(origins), tuple(facilities), threshold, tuple(sorted(closed_way_ids)))
        if key in self.cached:
            return list(self.cached[key])
        graph = self._matrix(closed_way_ids)
        nodes = self.base.data.nodes
        targets = []
        for facility in facilities:
            target = self._attach(facility, nodes, graph)
            if target is not None:
                targets.append((facility, *target))
        rows = [self._unknown(origin) for origin in origins]
        if targets:
            shortest = np.full(len(origins), np.inf)
            assigned: list[str | None] = [None] * len(origins)
            valid = np.array(
                [
                    o.node if o.node is not None and 0 <= o.node < graph.shape[0] else 0
                    for o in origins
                ],
                dtype=np.int64,
            )
            if len(targets) > 1:
                shortest, owners = nearest_targets(
                    graph, [(node, offset) for _, node, offset in targets], valid
                )
                assigned = [targets[int(owner)][0].id if owner >= 0 else None for owner in owners]
            else:
                for facility, node, snap_hours in targets:
                    distances = dijkstra(graph, directed=True, indices=node)[valid] + snap_hours
                    better = distances < shortest
                    shortest[better] = distances[better]
                    for improved in np.flatnonzero(better):
                        assigned[int(improved)] = facility.id
            complete = len(targets) == len(facilities) and all(
                f.coordinate_status
                in {"verified_entrance_complete_inventory", "verified_fire_exit_complete_inventory"}
                for f in facilities
            )
            for index, origin in enumerate(origins):
                if origin.node is None or origin.node < 0 or origin.node >= graph.shape[0]:
                    continue
                if origin.snap_km is None or not 0 <= origin.snap_km <= 5:
                    continue
                value = float(shortest[index]) + origin.snap_km / self.approach_speed_kmh
                if np.isfinite(value):
                    minutes = value * 60
                    state: AccessState = (
                        "within" if minutes <= threshold else "exceeded" if complete else "unknown"
                    )
                    rows[index] = replace(
                        rows[index],
                        facility_id=assigned[index],
                        minutes=minutes,
                        excess_minutes=max(0, minutes - threshold),
                        state=state,
                    )
                elif complete:
                    rows[index] = replace(rows[index], state="unreachable")
        if len(self.cached) >= 4:
            self.cached.pop(next(iter(self.cached)))
        self.cached[key] = rows
        return list(rows)

    def _attach(
        self, facility: Facility, nodes: dict[str, object], graph: object
    ) -> tuple[int, float] | None:
        if facility.latitude is None or facility.longitude is None:
            return None
        lat, lon = np.asarray(nodes["lat"]), np.asarray(nodes["lon"])
        if self.attachment_index is None:
            order = np.argsort(lat)
            self.attachment_index = order, lat[order]
        order, sorted_lat = self.attachment_index
        start, end = np.searchsorted(
            sorted_lat, [facility.latitude - 0.003, facility.latitude + 0.003]
        )
        nearby = order[start:end]
        nearby = nearby[
            (abs(lat[nearby] - facility.latitude) < 0.003)
            & (abs(lon[nearby] - facility.longitude) < 0.006)
        ]
        if not len(nearby):
            return None
        nearby = np.sort(nearby)
        km = 111.195 * np.hypot(
            lat[nearby] - facility.latitude,
            (lon[nearby] - facility.longitude) * np.cos(np.deg2rad(facility.latitude)),
        )
        index = int(np.argmin(km))
        return (
            (int(nearby[index]), float(km[index]) / self.approach_speed_kmh)
            if km[index] <= 0.25
            else None
        )

    def _unknown(self, origin: Origin) -> AccessRow:
        return AccessRow(
            origin.id,
            origin.name,
            origin.population,
            origin.latitude,
            origin.longitude,
            None,
            None,
            None,
            "unknown",
            routing_node=origin.node,
            approach_metres=origin.snap_km * 1000 if origin.snap_km is not None else None,
        )

    def _matrix(self, closed_way_ids: list[int]) -> Any:
        self.base.prepare()
        graph = self.base.graph
        if closed_way_ids:
            way_rows = self.base.data.read("way_indices", {"ids": closed_way_ids})
            if {int(r[0]) for r in way_rows} != set(closed_way_ids):
                raise InvalidQuery("Unknown road way in closure scenario")
            ways = {int(r[0]): int(r[1]) for r in way_rows}
            graph = road_closure_matrix(
                graph,
                self.base.data.edges,
                self.base.data.allowed_edges("road"),
                list(ways.values()),
            )
        return graph

    def missing_ways(self, ids: list[int]) -> list[int]:
        if not ids:
            return []
        found = {int(row[0]) for row in self.base.data.read("way_indices", {"ids": ids})}
        return [value for value in ids if value not in found]

    def trace(
        self, origin: Origin, facility: Facility, closed_way_ids: list[int], revision: str
    ) -> RouteGeometry:
        with self.lock:
            if revision != self.revision:
                raise DataUnavailable("The saved road graph revision is unavailable")
            graph = self._matrix(closed_way_ids)
            target = self._attach(facility, self.base.data.nodes, graph)
            if origin.node is None or origin.snap_km is None or target is None:
                raise DataUnavailable("The saved road attachments are unavailable")
            if not 0 <= origin.node < graph.shape[0] or not 0 <= origin.snap_km <= 5:
                raise DataUnavailable("The saved road attachment is invalid")
            distances, predecessors = dijkstra(
                graph, directed=True, indices=origin.node, return_predecessors=True
            )
            node, offset = target
            if not np.isfinite(distances[node]):
                raise DataUnavailable("No road route exists in this snapshot")
            path = predecessor_path(predecessors, origin.node, node)
            nodes = self.base.data.nodes
            if any(index >= len(np.asarray(nodes["lat"])) for index in path):
                raise DataUnavailable("The saved road path has incomplete node geometry")
            points = [
                (float(np.asarray(nodes["lon"])[index]), float(np.asarray(nodes["lat"])[index]))
                for index in path
            ]
            minutes = (
                float(distances[node]) + offset + origin.snap_km / self.approach_speed_kmh
            ) * 60
            return geometry(points, origin, facility, minutes=minutes)
