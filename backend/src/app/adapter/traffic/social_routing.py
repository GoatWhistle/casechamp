from typing import Any

import numpy as np
from scipy.spatial import cKDTree
from synthetic_traffic.model import Network

from app.adapter.normative.nearest_targets import nearest_targets
from app.adapter.normative.origin_attachment import sphere
from app.adapter.road_graph.weighted import minimum_csr
from app.domain.normative.model import AccessRow, Facility


class SocialRouting:
    def __init__(self, network: Network) -> None:
        self.network = network
        allowed = np.unique(np.r_[network.source, network.target])
        if network.access_raw_nodes is not None:
            allowed = allowed[np.isin(network.raw_nodes[allowed], network.access_raw_nodes)]
        self.nodes = allowed
        self.tree = cKDTree(sphere(network.lat[allowed], network.lon[allowed])) if len(allowed) else None

    def targets(self, facilities: list[Facility]) -> list[tuple[Facility, int, float]]:
        located = [facility for facility in facilities if facility.latitude is not None
                   and facility.longitude is not None]
        if self.tree is None or not located:
            return []
        chord, index = self.tree.query(sphere(
            np.array([f.latitude for f in located]), np.array([f.longitude for f in located]),
        ))
        km = 2 * 6371.0088 * np.arcsin(np.minimum(1, chord / 2))
        return [(facility, int(self.nodes[position]), float(distance / 15))
                for facility, position, distance in zip(located, index, km, strict=True)
                if np.isfinite(distance) and distance <= .25]

    def matrix(self, network: Network, hours: Any) -> Any:
        if not np.array_equal(network.raw_nodes, self.network.raw_nodes):
            raise ValueError("Social scenarios must preserve network node identities")
        weights = np.asarray(hours, dtype=float)
        if len(weights) != len(network.source) or np.any(np.isnan(weights)) or np.any(weights < 0):
            raise ValueError("Social routing weights must match nonnegative scenario hours")
        finite = np.isfinite(weights)
        return minimum_csr(network.source[finite], network.target[finite], weights[finite],
                           len(network.raw_nodes), directed=True)

    def evaluate(
        self, matrix: Any, rows: list[AccessRow], targets: list[tuple[Facility, int, float]],
    ) -> list[tuple[float | None, str | None, bool]]:
        raw = self.network.raw_nodes
        requested = np.array([row.routing_node if row.routing_node is not None else -1 for row in rows])
        nodes = np.searchsorted(raw, requested)
        valid = nodes < len(raw)
        valid[valid] &= raw[nodes[valid]] == requested[valid]
        valid &= np.array([row.approach_metres is not None and 0 <= row.approach_metres <= 5000
                           for row in rows], dtype=bool)
        result: list[tuple[float | None, str | None, bool]] = [(None, None, False)] * len(rows)
        if not targets or not valid.any():
            return result
        distances, owners = nearest_targets(matrix, [(node, offset) for _, node, offset in targets], nodes[valid])
        for index, distance, owner in zip(np.flatnonzero(valid), distances, owners, strict=True):
            if not np.isfinite(distance) or owner < 0:
                result[int(index)] = (None, None, True)
            else:
                minutes = (float(distance) + float(rows[index].approach_metres or 0) / 15000) * 60
                result[int(index)] = (minutes, targets[int(owner)][0].id, True)
        return result
