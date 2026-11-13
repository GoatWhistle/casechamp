from synthetic_traffic.incremental import IncrementalBaseline

from app.usecase.traffic import TrafficRoad


def baseline_roads(baseline: IncrementalBaseline, selected: list[int]) -> list[TrafficRoad]:
    graph, assignment = baseline.network, baseline.assignment
    lookup = {(int(graph.source[i]), int(graph.target[i]), int(graph.way_id[i])): i for i in selected}
    visible = sorted(selected, key=lambda edge: -assignment.ratio[edge])[:800]
    return [TrafficRoad(int(graph.way_id[i]), [
        [float(graph.lon[graph.source[i]]), float(graph.lat[graph.source[i]])],
        [float(graph.lon[graph.target[i]]), float(graph.lat[graph.target[i]])],
    ], float(assignment.flow[i]), float(assignment.flow[i]), float(assignment.ratio[i]),
        float(assignment.ratio[i]), edge_index=i,
        reverse_edge_index=lookup.get((int(graph.target[i]), int(graph.source[i]), int(graph.way_id[i]))),
        model_lanes=round(float(graph.capacity[i]) / 1800), shared_lane=bool(graph.shared[i] >= 0),
    ) for i in visible]
