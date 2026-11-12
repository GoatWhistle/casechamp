from threading import Lock

import numpy as np

from app.adapter.normative.routing import GraphNormativeRouting
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.routing import minimum_csr
from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.fire import FireProfile
from app.domain.normative.model import Facility, Origin
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.route import RouteGeometry


class FireNormativeRouting(GraphNormativeRouting):
    def __init__(self, base: DeltaBase, profile: FireProfile) -> None:
        super().__init__(base, approach_speed_kmh=profile.speed_kmh)
        self.profile = profile
        self.matrix_cache: tuple[tuple[int, ...], object] | None = None

    def trace(
        self, origin: Origin, facility: Facility, closed_way_ids: list[int], revision: str
    ) -> RouteGeometry:
        traced = super().trace(origin, facility, closed_way_ids, revision)
        return RouteGeometry(
            list(reversed(traced.network_coordinates)),
            [list(reversed(line)) for line in reversed(traced.approaches)],
            traced.minutes,
            traced.distance_metres,
        )

    def _matrix(self, closed_way_ids: list[int]) -> object:
        key = tuple(sorted(set(closed_way_ids)))
        if self.matrix_cache is not None and self.matrix_cache[0] == key:
            return self.matrix_cache[1]
        self.base.prepare()
        edges = self.base.data.edges
        if "km" not in edges:
            raise DataUnavailable("Fire routing requires sourced edge lengths")
        keep = self.base.data.allowed_edges("road").copy()
        if closed_way_ids:
            rows = self.base.data.read("way_indices", {"ids": closed_way_ids})
            if {int(row[0]) for row in rows} != set(closed_way_ids):
                raise InvalidQuery("Unknown road way in fire closure scenario")
            indices = [int(row[1]) for row in rows]
            keep &= ~np.isin(edges["way_idx"], indices)
        lengths = np.asarray(edges["km"], dtype=np.float64)
        if np.any(~np.isfinite(lengths[keep])) or np.any(lengths[keep] < 0):
            raise DataUnavailable("Fire routing edge lengths are invalid")
        matrix = minimum_csr(
            edges["src"][keep],
            edges["dst"][keep],
            lengths[keep] / self.profile.speed_kmh,
            self.base.graph.shape[0],
        )
        self.matrix_cache = (key, matrix)
        return matrix


class FireRoutingFactory:
    def __init__(self, base: DeltaBase) -> None:
        self.base = base
        self.cached: FireNormativeRouting | None = None
        self.lock = Lock()

    def with_profile(self, profile: FireProfile) -> NormativeRouting:
        with self.lock:
            if self.cached is None or self.cached.profile != profile:
                self.cached = FireNormativeRouting(self.base, profile)
            return self.cached
