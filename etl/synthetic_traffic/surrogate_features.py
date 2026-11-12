from dataclasses import dataclass, field
from heapq import heappop, heappush
from time import monotonic

import numpy as np
from synthetic_traffic.assignment import Assignment, route_graph
from synthetic_traffic.model import Network

CONNECTION_FEATURES = [
    "new_connections",
    "endpoint_hours",
    "unreachable_directions",
    "proposed_hours",
    "endpoint_flow_sum",
    "endpoint_flow_min",
    "endpoint_delay",
    "endpoint_ratio",
    "potential_vehicle_hours",
    "proposed_capacity",
]


@dataclass
class FeatureContext:
    network: Network
    baseline: Assignment
    deadline: float | None = None
    check: object = None
    distances: dict = field(default_factory=dict)

    def __post_init__(self):
        self.checkpoint()
        n = self.network
        self.nodes = {int(raw): i for i, raw in enumerate(n.raw_nodes)}
        self.graph, _ = route_graph(n, self.baseline.hours)
        size = len(n.raw_nodes)
        self.flow = np.bincount(n.source, weights=self.baseline.flow, minlength=size)
        self.flow += np.bincount(n.target, weights=self.baseline.flow, minlength=size)
        delay = self.baseline.flow * np.maximum(self.baseline.hours - n.free_hours, 0)
        self.delay = np.bincount(n.source, weights=delay, minlength=size)
        self.delay += np.bincount(n.target, weights=delay, minlength=size)
        self.ratio = np.zeros(size)
        np.maximum.at(self.ratio, n.source, self.baseline.ratio)
        np.maximum.at(self.ratio, n.target, self.baseline.ratio)
        self.checkpoint()

    def checkpoint(self):
        if self.check is not None:
            self.check()
        if self.deadline is not None and monotonic() >= self.deadline:
            raise TimeoutError("Surrogate feature budget expired")

    def distance(self, source, target):
        self.checkpoint()
        key = (source, target)
        if key in self.distances:
            return self.distances[key]
        queue, distances, visited = [(0.0, source)], {source: 0.0}, 0
        result = float("inf")
        graph = self.graph
        while queue:
            distance, node = heappop(queue)
            if distance != distances[node]:
                continue
            visited += 1
            if visited % 128 == 0:
                self.checkpoint()
            if node == target:
                result = distance
                break
            for edge in range(graph.indptr[node], graph.indptr[node + 1]):
                nxt = int(graph.indices[edge])
                value = distance + graph.data[edge]
                if value < distances.get(nxt, float("inf")):
                    distances[nxt] = value
                    heappush(queue, (value, nxt))
        self.distances[key] = result
        return result


def build_feature_context(network, baseline, deadline=None, check=None):
    return FeatureContext(network, baseline, deadline, check)


def connection_features(context, parts):
    result = np.zeros(len(CONNECTION_FEATURES))
    for part in parts:
        if part["kind"] not in {"connection", "opening"}:
            continue
        if "source_node" not in part or "target_node" not in part:
            continue
        a = context.nodes[int(part["source_node"])]
        b = context.nodes[int(part["target_node"])]
        times = np.asarray([context.distance(a, b), context.distance(b, a)])
        finite = times[np.isfinite(times)]
        hours = float(part["length_km"]) / float(part.get("speed_kmh", 40))
        supplied = part.get("free_travel_hours")
        segments = part.get("travel_segments")
        if supplied is not None and not np.isclose(
            hours, float(supplied), rtol=1e-5, atol=1e-8
        ):
            raise ValueError(
                "Proposed travel time disagrees with applied equivalent speed"
            )
        if segments:
            total = sum(float(segment["free_hours"]) for segment in segments)
            if not np.isclose(hours, total, rtol=1e-5, atol=1e-8):
                raise ValueError(
                    "Segment travel times disagree with applied equivalent speed"
                )
        flow = context.flow[[a, b]]
        old = float(finite.mean()) if len(finite) else 0.0
        result += [
            1,
            old,
            2 - len(finite),
            hours,
            flow.sum(),
            flow.min(),
            context.delay[[a, b]].sum(),
            context.ratio[[a, b]].max(),
            max(old - hours, 0) * flow.min(),
            float(part.get("capacity_vph", 1800)),
        ]
    return result.tolist()
