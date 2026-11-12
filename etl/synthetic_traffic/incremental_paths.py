from collections.abc import Callable
from dataclasses import dataclass
from heapq import heappop, heappush
from time import monotonic

import numpy as np
from numpy.typing import NDArray
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.model import Network, Trip


def checkpoint(deadline: float | None, check: Callable[[], None] | None = None) -> None:
    if check is not None:
        check()
    if deadline is not None and monotonic() >= deadline:
        raise TimeoutError("Traffic search deadline reached")


@dataclass
class Tree:
    distance: NDArray[np.float64]
    parent: NDArray[np.int64]


class PathCache:
    def __init__(
        self,
        network: Network,
        trips: list[Trip],
        hours: NDArray[np.float64],
        deadline: float | None = None,
        check: Callable[[], None] | None = None,
    ):
        self.trips = trips
        self.entries: dict[int, list[tuple[int, Trip]]] = {}
        for index, trip in enumerate(trips):
            self.entries.setdefault(trip.origin, []).append((index, trip))
        self.edges = self.edge_map(network, hours)
        graph, _ = route_graph(network, hours)
        self.trees = {}
        for origin in self.entries:
            checkpoint(deadline, check)
            distance, parent = dijkstra(
                graph, directed=True, indices=origin, return_predecessors=True
            )
            self.trees[origin] = Tree(distance, parent.astype(np.int64))
        self.repaired_origins = 0
        self.changed_nodes = 0
        self._shared_trees: set[int] = set()
        self.loads: dict[
            int, tuple[dict[tuple[int, int], float], float, dict[int, float]]
        ] = {}

    @staticmethod
    def edge_map(
        network: Network, hours: NDArray[np.float64]
    ) -> dict[tuple[int, int], tuple[float, int]]:
        _, chosen = route_graph(network, hours)
        return {
            (int(network.source[e]), int(network.target[e])): (float(hours[e]), int(e))
            for e in chosen
        }

    def fork(self) -> "PathCache":
        result = object.__new__(PathCache)
        result.trips, result.entries = self.trips, self.entries
        result.edges = self.edges
        result.trees = self.trees.copy()
        self._shared_trees.update(self.trees)
        result._shared_trees = set(self.trees)
        result.repaired_origins = result.changed_nodes = 0
        result.loads = self.loads.copy()
        return result

    def update(
        self,
        network: Network,
        hours: NDArray[np.float64],
        deadline: float | None = None,
    ) -> None:
        new = self.edge_map(network, hours)
        self._update_edges(new, deadline)

    def _update_edges(
        self,
        new: dict[tuple[int, int], tuple[float, int]],
        deadline: float | None = None,
    ) -> None:
        changed = {
            key
            for key in self.edges.keys() | new.keys()
            if self.edges.get(key) != new.get(key)
        }
        incoming: dict[int, list[tuple[int, float]]] = {}
        outgoing: dict[int, list[tuple[int, float]]] = {}
        for (u, v), (weight, _) in new.items():
            incoming.setdefault(v, []).append((u, weight))
            outgoing.setdefault(u, []).append((v, weight))
        for origin, tree in self.trees.items():
            checkpoint(deadline)
            invalid = {
                v
                for u, v in changed
                if tree.parent[v] == u
                and (u, v) in self.edges
                and ((u, v) not in new or new[u, v][0] > self.edges[u, v][0])
            }
            improved = [
                (u, v, new[u, v][0])
                for u, v in changed
                if (u, v) in new
                and ((u, v) not in self.edges or new[u, v][0] < self.edges[u, v][0])
                and tree.distance[u] + new[u, v][0] < tree.distance[v]
            ]
            if not invalid and not improved:
                continue
            if origin in self._shared_trees:
                tree = Tree(tree.distance.copy(), tree.parent.copy())
                self.trees[origin] = tree
                self._shared_trees.remove(origin)
            self.repaired_origins += 1
            self.loads.pop(origin, None)
            children: dict[int, list[int]] = {}
            if invalid:
                for v in np.flatnonzero(tree.parent >= 0):
                    children.setdefault(int(tree.parent[v]), []).append(int(v))
                pending = list(invalid)
                while pending:
                    checkpoint(deadline)
                    for child in children.get(pending.pop(), []):
                        if child not in invalid:
                            invalid.add(child)
                            pending.append(child)
            for v in invalid:
                tree.distance[v], tree.parent[v] = np.inf, -9999
            heap: list[tuple[float, int, int]] = []
            for v in invalid:
                for u, weight in incoming.get(v, []):
                    if u not in invalid and np.isfinite(tree.distance[u]):
                        heappush(heap, (float(tree.distance[u] + weight), v, u))
            for u, v, weight in improved:
                if np.isfinite(tree.distance[u]):
                    heappush(heap, (float(tree.distance[u] + weight), v, u))
            while heap:
                checkpoint(deadline)
                distance, v, parent = heappop(heap)
                if distance >= tree.distance[v]:
                    continue
                tree.distance[v], tree.parent[v] = distance, parent
                self.changed_nodes += 1
                for target, weight in outgoing.get(v, []):
                    if distance + weight < tree.distance[target]:
                        heappush(heap, (distance + weight, target, v))
        self.edges = new

    def load(
        self, network: Network, deadline: float | None = None
    ) -> tuple[NDArray[np.float64], float, list[float | None]]:
        flow = np.zeros(len(network.source))
        times: list[float | None] = [None] * len(self.trips)
        missing = 0.0
        for origin in self.entries:
            checkpoint(deadline)
            if origin not in self.loads:
                self.loads[origin] = self._load_origin(origin)
            amounts, lost, reached = self.loads[origin]
            missing += lost
            for index, value in reached.items():
                times[index] = value
            for pair, amount in amounts.items():
                flow[self.edges[pair][1]] += amount
        return flow, missing, times

    def _load_origin(
        self, origin: int
    ) -> tuple[dict[tuple[int, int], float], float, dict[int, float]]:
        tree = self.trees[origin]
        pending = np.zeros(len(tree.parent))
        missing = 0.0
        times = {}
        amounts = {}
        for index, trip in self.entries[origin]:
            if np.isfinite(tree.distance[trip.destination]):
                times[index] = float(tree.distance[trip.destination])
                pending[trip.destination] += trip.vehicles_per_hour
            else:
                missing += trip.vehicles_per_hour
        nodes = np.flatnonzero(tree.parent >= 0)
        for node in nodes[np.argsort(-tree.distance[nodes])]:
            amount = pending[node]
            if amount:
                parent = int(tree.parent[node])
                amounts[parent, int(node)] = float(amount)
                pending[parent] += amount
        return amounts, missing, times


class GraphCache(PathCache):
    def __init__(
        self,
        graph,
        origins,
        deadline: float | None = None,
        check: Callable[[], None] | None = None,
    ):
        self.edges = self.csr_edges(graph)
        self.trees = {}
        self.entries = {}
        self.trips = []
        self.loads = {}
        self.repaired_origins = self.changed_nodes = 0
        self._shared_trees = set()
        for origin in origins:
            checkpoint(deadline, check)
            distance, parent = dijkstra(
                graph, directed=True, indices=int(origin), return_predecessors=True
            )
            self.trees[int(origin)] = Tree(distance, parent.astype(np.int64))

    @staticmethod
    def csr_edges(graph):
        matrix = graph.tocsr(copy=True)
        matrix.sum_duplicates()
        return {
            (u, int(matrix.indices[i])): (float(matrix.data[i]), i)
            for u in range(matrix.shape[0])
            for i in range(matrix.indptr[u], matrix.indptr[u + 1])
        }

    def update_graph(self, graph, deadline: float | None = None) -> None:
        if (
            self.trees
            and graph.shape != (len(next(iter(self.trees.values())).parent),) * 2
        ):
            raise ValueError("Incremental graph must preserve node count")
        self._update_edges(self.csr_edges(graph), deadline)

    def fork(self) -> "GraphCache":
        result = super().fork()
        result.__class__ = GraphCache
        return result
