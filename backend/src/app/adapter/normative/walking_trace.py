import numpy as np
from scipy.sparse.csgraph import dijkstra

from app.adapter.normative.path_geometry import geometry, predecessor_path
from app.adapter.normative.walking_graph import FACILITY_LIMIT_METRES, WalkingGraph
from app.domain.errors import DataUnavailable
from app.domain.normative.model import Facility, Origin
from app.usecase.normative.route import RouteGeometry


def trace_walking(
    graph: WalkingGraph,
    origin: Origin,
    facility: Facility,
    closed_way_ids: list[int],
) -> RouteGeometry:
    weights = graph.weights(closed_way_ids)
    projection = graph.attach(facility.latitude, facility.longitude, FACILITY_LIMIT_METRES)
    target = projection.costs(weights, False) if projection is not None else []
    if origin.node is None or origin.snap_km is None or not target:
        raise DataUnavailable("The saved pedestrian attachments are unavailable")
    count = len(graph.coordinates)
    if not 0 <= origin.node < count or not 0 <= origin.snap_km * 1000 <= graph.max_approach_metres:
        raise DataUnavailable("The saved pedestrian attachment is invalid")
    matrix = graph.matrix(weights, [target])
    distances, predecessors = dijkstra(
        matrix, directed=True, indices=origin.node, return_predecessors=True
    )
    if not np.isfinite(distances[count]):
        raise DataUnavailable("No pedestrian route exists in this snapshot")
    path = predecessor_path(predecessors, origin.node, count)
    points = [
        (float(graph.coordinates[node, 1]), float(graph.coordinates[node, 0]))
        for node in path
        if node < count
    ]
    return geometry(
        points, origin, facility, metres=float(distances[count]) + origin.snap_km * 1000
    )
