from dataclasses import replace
from threading import Lock

import numpy as np
from scipy.spatial import cKDTree

from app.adapter.road_graph.delta_base import DeltaBase
from app.domain.errors import DataUnavailable
from app.domain.normative.model import Origin


def sphere(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat, lon = np.deg2rad(latitude), np.deg2rad(longitude)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


class GraphOriginAttachment:
    def __init__(self, base: DeltaBase) -> None:
        self.base = base
        self.lock = Lock()
        self.tree: cKDTree | None = None
        self.index_revision: str | None = None
        self.nodes = np.array([], dtype=np.int64)

    def attach(self, origins: list[Origin], revision: str) -> list[Origin]:
        with self.lock:
            if revision != self.base.data.revision:
                raise DataUnavailable(
                    "The requested object attachment graph revision is unavailable"
                )
            self.base.prepare()
            if self.index_revision is None:
                self._prepare()
                self.index_revision = revision
            elif self.index_revision != revision:
                raise DataUnavailable("The attachment index belongs to another graph revision")
            result = []
            for origin in origins:
                node, distance = None, None
                if (
                    self.tree is not None
                    and origin.latitude is not None
                    and origin.longitude is not None
                ):
                    chord, index = self.tree.query(
                        sphere(np.array([origin.latitude]), np.array([origin.longitude]))[0]
                    )
                    km = float(2 * 6371.0088 * np.arcsin(min(1.0, chord / 2)))
                    if np.isfinite(km) and km <= 0.25:
                        node, distance = int(self.nodes[index]), km
                result.append(replace(origin, node=node, snap_km=distance))
            return result

    def _prepare(self) -> None:
        edges = self.base.data.edges
        allowed = self.base.data.allowed_edges("road")
        nodes = np.unique(np.concatenate((edges["src"][allowed], edges["dst"][allowed])))
        lat, lon = np.asarray(self.base.data.nodes["lat"]), np.asarray(self.base.data.nodes["lon"])
        if np.any(nodes < 0) or np.any(nodes >= len(lat)) or len(lat) != len(lon):
            raise DataUnavailable("Road nodes have incomplete attachment geometry")
        valid = (
            np.isfinite(lat[nodes])
            & np.isfinite(lon[nodes])
            & (abs(lat[nodes]) <= 90)
            & (abs(lon[nodes]) <= 180)
        )
        self.nodes = nodes[valid].astype(np.int64)
        if len(self.nodes):
            self.tree = cKDTree(sphere(lat[self.nodes], lon[self.nodes]))
