from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf, isfinite, isnan
from typing import Any


@dataclass(frozen=True)
class RoadPath:
    nodes: list[int]
    hours: float
    settled_nodes: int


def bidirectional_path(
    graph: Any, source: int, target: int, reverse: Any = None
) -> RoadPath | None:
    if not 0 <= source < graph.shape[0] or not 0 <= target < graph.shape[0]:
        raise ValueError("Route endpoint is outside the graph")
    if source == target:
        return RoadPath([source], 0.0, 0)
    backward = graph.transpose().tocsr() if reverse is None else reverse
    networks = (graph, backward)
    queues: list[list[tuple[float, int]]] = [[(0.0, source)], [(0.0, target)]]
    distances = [{source: 0.0}, {target: 0.0}]
    parents: list[dict[int, int]] = [{}, {}]
    settled: list[set[int]] = [set(), set()]
    best, meeting = inf, -1
    while queues[0] and queues[1]:
        for direction in (0, 1):
            queue = queues[direction]
            while queue and (
                queue[0][1] in settled[direction]
                or queue[0][0] != distances[direction].get(queue[0][1])
            ):
                heappop(queue)
        if not queues[0] or not queues[1] or queues[0][0][0] + queues[1][0][0] >= best:
            break
        direction = 0 if queues[0][0][0] <= queues[1][0][0] else 1
        distance, node = heappop(queues[direction])
        settled[direction].add(node)
        network = networks[direction]
        start, end = network.indptr[node : node + 2]
        for position in range(int(start), int(end)):
            neighbor = int(network.indices[position])
            weight = float(network.data[position])
            if weight < 0 or isnan(weight):
                raise ValueError("Road search requires nonnegative weights")
            candidate = distance + weight
            if candidate >= distances[direction].get(neighbor, inf):
                continue
            distances[direction][neighbor] = candidate
            parents[direction][neighbor] = node
            heappush(queues[direction], (candidate, neighbor))
            joined = candidate + distances[1 - direction].get(neighbor, inf)
            if joined < best:
                best, meeting = joined, neighbor
    if not isfinite(best):
        return None
    left = [meeting]
    while left[-1] != source:
        left.append(parents[0][left[-1]])
    path = list(reversed(left))
    while path[-1] != target:
        path.append(parents[1][path[-1]])
    return RoadPath(path, best, len(settled[0]) + len(settled[1]))
