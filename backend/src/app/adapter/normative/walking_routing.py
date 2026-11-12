from dataclasses import replace
from threading import Lock

import numpy as np
from scipy.sparse.csgraph import dijkstra

from app.adapter.normative.walking_graph import (
    FACILITY_LIMIT_METRES,
    ORIGIN_LIMIT_METRES,
    Attachment,
    WalkingGraph,
)
from app.adapter.normative.walking_trace import trace_walking
from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import AccessRow, Facility, Origin
from app.usecase.normative.route import RouteGeometry
from app.usecase.normative.walking import PedestrianRepository


class WalkingNormativeRouting:
    def __init__(self, repository: PedestrianRepository, spherical: bool = False) -> None:
        self.repository = repository
        self.spherical = spherical
        self.graph: WalkingGraph | None = None
        self.lock = Lock()
        self.archived: dict[str, WalkingGraph] = {}

    def prepare(self) -> WalkingGraph:
        if self.graph is None:
            self.graph = WalkingGraph(self.repository.network(), self.spherical)
        return self.graph

    @property
    def revision(self) -> str:
        with self.lock:
            return self.prepare().network.revision

    def evaluate(
        self,
        origins: list[Origin],
        facilities: list[Facility],
        threshold: float,
        closed_way_ids: list[int],
    ) -> list[AccessRow]:
        if threshold <= 0:
            raise InvalidQuery("Walking reference threshold must be positive")
        with self.lock:
            return self._evaluate(origins, facilities, closed_way_ids)

    def _evaluate(
        self, origins: list[Origin], facilities: list[Facility], closed_way_ids: list[int]
    ) -> list[AccessRow]:
        graph = self.prepare()
        weights = graph.weights(closed_way_ids)
        targets: list[tuple[Facility, Attachment]] = []
        for facility in facilities:
            projection = graph.attach(facility.latitude, facility.longitude, FACILITY_LIMIT_METRES)
            if projection is not None:
                targets.append((facility, projection.costs(weights, False)))
        if not targets:
            raise DataUnavailable("No facility can be attached to the pedestrian graph within 250m")
        matrix = graph.matrix(weights, [target[1] for target in targets])
        count = len(graph.coordinates)
        distances, _, sources = dijkstra(
            matrix.T.tocsr(),
            directed=True,
            indices=np.arange(count, count + len(targets)),
            min_only=True,
            return_predecessors=True,
        )
        projections = graph.attach_many(
            np.array([np.nan if o.latitude is None else o.latitude for o in origins]),
            np.array([np.nan if o.longitude is None else o.longitude for o in origins]),
            ORIGIN_LIMIT_METRES,
        )
        rows = []
        for origin, projection in zip(origins, projections, strict=True):
            entry = AccessRow(
                origin.id,
                origin.name,
                None,
                origin.latitude,
                origin.longitude,
                None,
                None,
                None,
                "unknown",
                uncertainty=(
                    *(
                        ("residential_reference_not_entrance",)
                        if not origin.entrance_verified
                        else ()
                    ),
                    "population_group_missing",
                    "territory_conditions_missing",
                    "facility_entrances_unverified",
                    "service_status_unconfirmed",
                ),
            )
            attachment = projection.costs(weights, True) if projection is not None else []
            if not attachment:
                rows.append(replace(entry, uncertainty=(*entry.uncertainty, "origin_unattached")))
                continue
            node, offset = min(attachment, key=lambda item: distances[item[0]] + item[1])
            entry = replace(entry, routing_node=node, approach_metres=offset)
            if not np.isfinite(distances[node]):
                rows.append(replace(entry, uncertainty=(*entry.uncertainty, "path_unconfirmed")))
                continue
            facility = targets[int(sources[node]) - count][0]
            if facility.coordinate_status in {
                "verified_entrance",
                "verified_entrance_complete_inventory",
            }:
                entry = replace(
                    entry,
                    uncertainty=tuple(
                        reason
                        for reason in entry.uncertainty
                        if reason != "facility_entrances_unverified"
                    ),
                )
            rows.append(
                replace(
                    entry, facility_id=facility.id, distance_metres=float(distances[node]) + offset
                )
            )
        return rows

    def missing_ways(self, ids: list[int]) -> list[int]:
        if not ids:
            return []
        with self.lock:
            ways = self.prepare().edges[:, 3]
            return [value for value in ids if not np.any(ways == value)]

    def trace(
        self, origin: Origin, facility: Facility, closed_way_ids: list[int], revision: str
    ) -> RouteGeometry:
        with self.lock:
            current = self.prepare()
            if current.network.revision == revision:
                graph = current
            else:
                if revision not in self.archived:
                    network = self.repository.network(revision)
                    if network.revision != revision:
                        raise DataUnavailable("The saved pedestrian revision is unavailable")
                    self.archived.clear()
                    self.archived[revision] = WalkingGraph(network, self.spherical)
                graph = self.archived[revision]
            return trace_walking(graph, origin, facility, closed_way_ids)
