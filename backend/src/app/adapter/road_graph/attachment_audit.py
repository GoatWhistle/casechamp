from __future__ import annotations

from collections.abc import Iterable
from functools import cached_property
from typing import Any, Protocol

import numpy as np
from scipy.sparse.csgraph import connected_components

from app.adapter.road_graph.weighted import minimum_csr
from app.domain.errors import DataUnavailable
from app.usecase.graph_snapshot import GraphParameters, GraphQuery


class AuditGraph(Protocol):
    edges: dict[str, Any]
    nodes: dict[str, Any]

    def load(self) -> None: ...
    def allowed_edges(self, scenario: str) -> Any: ...
    def indices_for(self, way_ids: list[int]) -> dict[int, int]: ...
    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]: ...


ATTACHMENT_AUDIT_VERSION = "settlement-attachment-audit-v1"


class SettlementAttachmentConflict(DataUnavailable):
    code = "settlement_attachment_conflict"
    message = "Settlement attachment cannot certify whole-settlement isolation"

    def __init__(self, point_ids: Iterable[str]) -> None:
        self.point_ids = tuple(point_ids)
        super().__init__(
            "Settlement attachment is cut off inside a surviving local street network: "
            + ", ".join(self.point_ids[:10])
            + ". Whole-settlement isolation and index loss cannot be certified from this attachment."
        )


def conflicting_attachment(
    edges: dict[str, Any],
    nodes: dict[str, Any],
    origin: int,
    closed_indices: set[int],
    allowed: Any = None,
) -> bool:
    lat, lon = float(nodes["lat"][origin]), float(nodes["lon"][origin])
    radius = 0.75
    nearby = np.flatnonzero(
        (np.abs(nodes["lat"] - lat) <= radius / 111.2)
        & (np.abs(nodes["lon"] - lon) <= radius / (111.2 * max(0.1, np.cos(np.radians(lat)))))
    )
    if len(nearby) < 12:
        return False
    inside = np.zeros(len(nodes["lat"]), dtype=bool)
    inside[nearby] = True
    selected = inside[edges["src"]] & inside[edges["dst"]]
    if allowed is not None:
        selected &= allowed
    positions = np.flatnonzero(selected)
    src = np.searchsorted(nearby, edges["src"][positions])
    dst = np.searchsorted(nearby, edges["dst"][positions])
    before = minimum_csr(src, dst, np.ones(len(src)), len(nearby))
    keep = ~np.isin(edges["way_idx"][positions], list(closed_indices))
    after = minimum_csr(src[keep], dst[keep], np.ones(int(keep.sum())), len(nearby))
    index = int(np.searchsorted(nearby, origin))
    _, baseline_labels = connected_components(before, directed=False)
    _, labels = connected_components(after, directed=False)
    baseline = baseline_labels == baseline_labels[index]
    detached = (labels == labels[index]) & baseline
    if detached.sum() > 4 or baseline.sum() < 12:
        return False
    remaining = np.flatnonzero(baseline & ~detached)
    for component in np.unique(labels[remaining]):
        block = np.flatnonzero(baseline & (labels == component))
        if len(block) >= 8 and after[block][:, block].nnz >= 2 * len(block):
            return True
    return False


class AttachmentAudit:
    def __init__(self, data: AuditGraph) -> None:
        self.data = data
        self.checked: dict[tuple[int, ...], tuple[str, ...]] = {}

    @cached_property
    def points(self) -> list[tuple[str, int]]:
        count = len(self.data.nodes["lat"])
        return [
            (str(point), int(node))
            for point, node, *_ in self.data.read("points")
            if node is not None and 0 <= int(node) < count
        ]

    def validate(self, way_ids: list[int]) -> None:
        if not way_ids:
            return
        key = tuple(sorted(set(way_ids)))
        if key not in self.checked:
            if len(self.checked) >= 256:
                self.checked.pop(next(iter(self.checked)))
            self.checked[key] = self.conflicts(list(key))
        if self.checked[key]:
            raise SettlementAttachmentConflict(self.checked[key])

    def conflicts(self, way_ids: list[int]) -> tuple[str, ...]:
        self.data.load()
        indices = set(self.data.indices_for(way_ids).values())
        edges, nodes = self.data.edges, self.data.nodes
        changed = np.isin(edges["way_idx"], list(indices))
        ends = np.unique(np.concatenate([edges["src"][changed], edges["dst"][changed]]))
        if not len(ends):
            return ()
        lat, lon = nodes["lat"][ends], nodes["lon"][ends]
        margin = 0.75 / 111.2
        lon_margin = margin / max(0.1, float(np.cos(np.radians(lat)).min()))
        south, north = float(lat.min() - margin), float(lat.max() + margin)
        west, east = float(lon.min() - lon_margin), float(lon.max() + lon_margin)
        failures = []
        allowed = self.data.allowed_edges("road")
        for point, origin in self.points:
            if not (
                south <= nodes["lat"][origin] <= north and west <= nodes["lon"][origin] <= east
            ):
                continue
            if conflicting_attachment(edges, nodes, origin, indices, allowed):
                failures.append(point)
        return tuple(failures)
