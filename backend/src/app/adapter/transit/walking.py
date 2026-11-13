from math import ceil, isfinite

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from app.adapter.normative.walking_graph import Projection, WalkingGraph
from app.domain.errors import InvalidQuery
from app.usecase.transit_walking import WalkingLink, WalkingPoint


class TransitWalking:
    def __init__(self, graph: WalkingGraph, speed_metres_per_second: float = 1.4) -> None:
        if not isfinite(speed_metres_per_second) or speed_metres_per_second <= 0:
            raise InvalidQuery('Walking speed must be positive and finite')
        self.graph = graph
        self.speed = speed_metres_per_second

    @property
    def revision(self) -> str:
        return self.graph.network.revision

    def measure(self, points: list[WalkingPoint], pairs: list[tuple[str, str]],
                maximum_metres: float) -> list[WalkingLink]:
        if not isfinite(maximum_metres) or maximum_metres <= 0:
            raise InvalidQuery('Walking limit must be positive and finite')
        by_id = {point.id: point for point in points}
        if len(by_id) != len(points) or any(a not in by_id or b not in by_id for a, b in pairs):
            raise InvalidQuery('Walking pairs require unique known point identifiers')
        projections = {}
        for point in points:
            if not isfinite(point.attachment_limit_metres) or point.attachment_limit_metres <= 0:
                raise InvalidQuery('Attachment limit must be positive and finite')
            projections[point.id] = self.graph.attach(point.latitude, point.longitude, point.attachment_limit_metres)
        weights = self.graph.weights([])
        grouped: dict[str, list[str]] = {}
        for source, target in pairs:
            grouped.setdefault(source, []).append(target)
        measured = {}
        for source, targets in grouped.items():
            origin = projections[source]
            attachments = origin.costs(weights, True) if origin is not None else []
            distances = None
            if attachments:
                matrix = self.graph.matrix(weights.T.tocsr(), [attachments]).T.tocsr()
                distances = dijkstra(matrix, directed=True, indices=len(self.graph.coordinates), limit=maximum_metres)
            for target in targets:
                destination = projections[target]
                exits = destination.costs(weights, False) if destination is not None else []
                if origin is None or destination is None or not attachments or not exits or distances is None:
                    measured[source, target] = WalkingLink(source, target, 'unattached', None, None)
                    continue
                metres = min(float(distances[node]) + offset for node, offset in exits)
                if (origin.left, origin.right) == (destination.left, destination.right):
                    metres = min(metres, same_segment_metres(origin, destination, weights))
                if not isfinite(metres) or metres > maximum_metres:
                    measured[source, target] = WalkingLink(source, target, 'outside_walking_limit', None, None)
                else:
                    measured[source, target] = WalkingLink(source, target, 'available', metres, ceil(metres / self.speed))
        return [measured[pair] for pair in pairs]


def same_segment_metres(origin: Projection, target: Projection, weights: csr_matrix) -> float:
    delta = target.share - origin.share
    if abs(delta) <= 1e-12:
        return origin.perpendicular + target.perpendicular
    edge = float(weights[origin.left, origin.right] if delta > 0 else weights[origin.right, origin.left])
    return origin.perpendicular + target.perpendicular + abs(delta) * edge if edge > 0 else np.inf
