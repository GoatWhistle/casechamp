from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

from app.usecase.normative.walking import PedestrianNetwork

ORIGIN_LIMIT_METRES = 150.0
FACILITY_LIMIT_METRES = 250.0
SAMPLE_SPACING_METRES = 25.0
CANDIDATES = 12
METRES_PER_DEGREE = 111_195.0

Attachment = list[tuple[int, float]]


@dataclass(frozen=True, slots=True)
class Projection:
    left: int
    right: int
    perpendicular: float
    share: float

    def costs(self, weights: Any, toward_network: bool) -> Attachment:
        result = []
        for node, other, fraction in (
            (self.left, self.right, self.share),
            (self.right, self.left, 1 - self.share),
        ):
            if fraction <= 1e-9:
                result.append((node, self.perpendicular))
                continue
            if fraction >= 1 - 1e-9:
                continue
            edge = float(weights[other, node] if toward_network else weights[node, other])
            if edge > 0:
                result.append((node, self.perpendicular + fraction * edge))
        return result


class WalkingGraph:
    def __init__(self, network: PedestrianNetwork, spherical: bool = False) -> None:
        self.network = network
        self.spherical = spherical
        self.coordinates = np.asarray([(row[1], row[2]) for row in network.nodes], dtype=np.float64)
        if [row[0] for row in network.nodes] != list(range(len(network.nodes))):
            raise ValueError("Pedestrian node indices must be contiguous")
        self.edges = np.asarray(network.edges)
        self.segments, self.lengths = undirected_segments(self.edges)
        self.max_approach_metres = ORIGIN_LIMIT_METRES + (
            float(self.edges[:, 2].max()) if len(self.edges) else 0.0
        )
        self.sample_segments, samples = segment_samples(
            self.coordinates, self.segments, SAMPLE_SPACING_METRES
        )
        self.tree = cKDTree(self.index_space(samples)) if len(samples) else None

    def index_space(self, coordinates: Any) -> Any:
        if self.spherical:
            return sphere(coordinates)
        return coordinates * np.array(
            [METRES_PER_DEGREE, METRES_PER_DEGREE * np.cos(np.deg2rad(55.5))]
        )

    def attach(
        self, latitude: float | None, longitude: float | None, limit: float = FACILITY_LIMIT_METRES
    ) -> Projection | None:
        if latitude is None or longitude is None:
            return None
        attached = self.attach_many(np.array([latitude]), np.array([longitude]), limit)
        return attached[0]

    def attach_many(self, latitudes: Any, longitudes: Any, limit: float) -> list[Projection | None]:
        points = np.column_stack((latitudes, longitudes)).astype(np.float64)
        valid = np.flatnonzero(np.isfinite(points).all(axis=1))
        result: list[Projection | None] = [None] * len(points)
        if self.tree is None or not len(valid):
            return result
        for i, attachment in zip(valid, self._attach_points(points[valid], limit), strict=True):
            result[int(i)] = attachment
        return result

    def _attach_points(self, points: Any, limit: float) -> list[Projection | None]:
        assert self.tree is not None
        count = len(points)
        k = min(CANDIDATES, self.tree.n)
        _, found = self.tree.query(self.index_space(points), k=k)
        candidates = self.sample_segments[np.asarray(found).reshape(count, k)]
        first = self.coordinates[self.segments[candidates, 0]]
        second = self.coordinates[self.segments[candidates, 1]]
        scale = np.cos(np.deg2rad(points[:, 0]))[:, None]
        origin_lat, origin_lon = points[:, 0][:, None], points[:, 1][:, None]
        ax = (first[..., 1] - origin_lon) * scale * METRES_PER_DEGREE
        ay = (first[..., 0] - origin_lat) * METRES_PER_DEGREE
        bx = (second[..., 1] - origin_lon) * scale * METRES_PER_DEGREE
        by = (second[..., 0] - origin_lat) * METRES_PER_DEGREE
        dx, dy = bx - ax, by - ay
        squared = dx * dx + dy * dy
        share = np.clip(
            np.divide(-(ax * dx + ay * dy), squared, out=np.zeros_like(squared), where=squared > 0),
            0,
            1,
        )
        offset = np.hypot(ax + share * dx, ay + share * dy)
        best = np.argmin(offset, axis=1)
        rows = np.arange(count)
        segment = candidates[rows, best]
        perpendicular = offset[rows, best]
        fraction = share[rows, best]
        result: list[Projection | None] = []
        for i in range(count):
            if not np.isfinite(perpendicular[i]) or perpendicular[i] > limit:
                result.append(None)
                continue
            left, right = (int(node) for node in self.segments[segment[i]])
            result.append(Projection(left, right, float(perpendicular[i]), float(fraction[i])))
        return result

    def weights(self, closed_way_ids: list[int]) -> Any:
        edges = self.edges
        selected = edges[~np.isin(edges[:, 3], closed_way_ids)]
        return directed_minimum(selected, len(self.coordinates))

    def matrix(self, weights: Any, attachments: list[Attachment]) -> Any:
        count = len(self.coordinates)
        graph = weights.tocoo()
        extra = np.array(
            [
                (node, count + i, cost)
                for i, attachment in enumerate(attachments)
                for node, cost in attachment
            ],
            dtype=np.float64,
        ).reshape(-1, 3)
        rows = np.concatenate([graph.row, extra[:, 0].astype(np.int64)])
        columns = np.concatenate([graph.col, extra[:, 1].astype(np.int64)])
        values = np.concatenate([graph.data, extra[:, 2]])
        size = count + len(attachments)
        return directed_minimum(np.column_stack((rows, columns, values)), size)


def undirected_segments(edges: Any) -> tuple[Any, Any]:
    if not len(edges):
        return np.empty((0, 2), dtype=np.int64), np.empty(0)
    pairs = np.sort(edges[:, :2].astype(np.int64), axis=1)
    keys, inverse = np.unique(pairs, axis=0, return_inverse=True)
    lengths = np.full(len(keys), np.inf)
    np.minimum.at(lengths, inverse.ravel(), edges[:, 2].astype(np.float64))
    return keys, lengths


def segment_samples(coordinates: Any, segments: Any, spacing: float) -> tuple[Any, Any]:
    if not len(segments):
        return np.empty(0, dtype=np.int64), np.empty((0, 2))
    first, second = coordinates[segments[:, 0]], coordinates[segments[:, 1]]
    scale = np.cos(np.deg2rad((first[:, 0] + second[:, 0]) / 2))
    planar = METRES_PER_DEGREE * np.hypot(
        second[:, 0] - first[:, 0], (second[:, 1] - first[:, 1]) * scale
    )
    pieces = np.maximum(1, np.ceil(planar / spacing)).astype(np.int64)
    owner = np.repeat(np.arange(len(segments)), pieces)
    starts = np.repeat(np.cumsum(pieces) - pieces, pieces)
    share = (np.arange(len(owner)) - starts + 0.5) / pieces[owner]
    points = first[owner] + (second[owner] - first[owner]) * share[:, None]
    return owner, points


def directed_minimum(edges: Any, count: int) -> Any:
    if not len(edges):
        return csr_matrix((count, count))
    keys = edges[:, 0].astype(np.int64) * count + edges[:, 1].astype(np.int64)
    order = np.argsort(keys, kind="stable")
    keys = keys[order]
    starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
    values = np.minimum.reduceat(edges[order, 2], starts)
    unique = keys[starts]
    return csr_matrix((values, (unique // count, unique % count)), shape=(count, count))


def sphere(coordinates: Any) -> Any:
    latitude, longitude = np.deg2rad(coordinates[:, 0]), np.deg2rad(coordinates[:, 1])
    return np.column_stack(
        (
            np.cos(latitude) * np.cos(longitude),
            np.cos(latitude) * np.sin(longitude),
            np.sin(latitude),
        )
    )
