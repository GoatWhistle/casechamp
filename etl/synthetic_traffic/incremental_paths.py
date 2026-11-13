from collections.abc import Callable, Mapping
from heapq import heappop, heappush
from pathlib import Path
from time import monotonic

import numpy as np
from numpy.typing import NDArray
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.edge_changes import edge_changes
from synthetic_traffic.edge_index import EdgeIndex
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.origin_store import OriginStore
from synthetic_traffic.tree_routing import bounded_tree, load_tree
from synthetic_traffic.tree_store import ArchiveTrees, Tree, TreeStore


def checkpoint(deadline: float | None, check: Callable[[], None] | None = None) -> None:
    if check is not None:
        check()
    if deadline is not None and monotonic() >= deadline:
        raise TimeoutError("Traffic search deadline reached")


class PathCache:
    def __init__(
        self,
        network: Network,
        trips: list[Trip],
        hours: NDArray[np.float64],
        deadline: float | None = None,
        check: Callable[[], None] | None = None,
        tree_directory: Path | None = None,
        path_limit: float = np.inf,
        progress: Callable[[dict], None] | None = None,
        replace_tree_cache: bool = False,
    ):
        if tree_directory is not None and not replace_tree_cache and any(tree_directory.glob('*.npz')):
            raise FileExistsError('Tree cache must be empty for a fresh baseline')
        self.progress = progress
        self.check = check
        self.trips = trips
        self.entries: dict[int, list[tuple[int, Trip]]] = {}
        for index, trip in enumerate(trips):
            self.entries.setdefault(trip.origin, []).append((index, trip))
        self.edges = self.edge_map(network, hours)
        graph, _ = route_graph(network, hours)
        self.trees = {} if tree_directory is None else TreeStore(tree_directory)
        for number, origin in enumerate(self.entries, 1):
            checkpoint(deadline, check)
            self.trees[origin] = bounded_tree(graph, origin,
                [trip.destination for _, trip in self.entries[origin]], path_limit)
            if progress is not None:
                progress({'stage': 'initial_paths', 'completed': number, 'total': len(self.entries)})
        self.repaired_origins = 0
        self.changed_nodes = 0
        self._shared_trees: set[int] = set()
        self.loads = {} if tree_directory is None else OriginStore(tree_directory.parent / 'loads', 'loads')
        if replace_tree_cache:
            self.loads.clear()

    @staticmethod
    def edge_map(
        network: Network, hours: NDArray[np.float64]
    ) -> EdgeIndex:
        _, chosen = route_graph(network, hours)
        size = len(network.raw_nodes)
        return EdgeIndex(network.source[chosen] * size + network.target[chosen],
                         hours[chosen], chosen, size)


    def fork(self) -> "PathCache":
        result = object.__new__(PathCache)
        result.trips, result.entries = self.trips, self.entries
        result.progress = getattr(self, "progress", None)
        result.check = getattr(self, "check", None)
        result.edges = self.edges
        result.trees = self.trees.fork() if isinstance(self.trees, (TreeStore, ArchiveTrees)) else self.trees.copy()
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
        new: Mapping[tuple[int, int], tuple[float, int]],
        deadline: float | None = None,
    ) -> None:
        changes = edge_changes(self.edges, new)
        if not len(changes.increased_source) and not len(changes.decreased_source):
            self.edges = new
            return
        if isinstance(new, EdgeIndex):
            incoming, outgoing = new.adjacency()
        else:
            incoming = {}
            outgoing = {}
            for (u, v), (weight, _) in new.items():
                incoming.setdefault(v, []).append((u, weight))
                outgoing.setdefault(u, []).append((v, weight))
        for number, (origin, tree) in enumerate(self.trees.items(), 1):
            progress = getattr(self, "progress", None)
            if progress is not None:
                progress({"stage": "repairing_paths", "completed": number - 1, "total": len(self.trees)})
            checkpoint(deadline, getattr(self, "check", None))
            invalid, improved = changes.affected(tree)
            if not invalid and not improved:
                continue
            if np.isfinite(tree.limit):
                graph = outgoing.matrix
                self.trees[origin] = bounded_tree(graph, origin,
                    [trip.destination for _, trip in self.entries[origin]], tree.limit)
                self.loads.pop(origin, None)
                self.repaired_origins += 1
                continue
            if origin in self._shared_trees:
                tree = Tree(tree.distance.copy(), tree.parent.copy(), tree.limit)
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
                    checkpoint(deadline, getattr(self, "check", None))
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
                checkpoint(deadline, getattr(self, "check", None))
                distance, v, parent = heappop(heap)
                if distance >= tree.distance[v]:
                    continue
                tree.distance[v], tree.parent[v] = distance, parent
                self.changed_nodes += 1
                for target, weight in outgoing.get(v, []):
                    if distance + weight < tree.distance[target]:
                        heappush(heap, (distance + weight, target, v))
            self.trees[origin] = tree
        progress = getattr(self, "progress", None)
        if progress is not None:
            progress({"stage": "repairing_paths", "completed": len(self.trees), "total": len(self.trees)})
        self.edges = new

    def load(
        self, network: Network, deadline: float | None = None
    ) -> tuple[NDArray[np.float64], float, list[float | None]]:
        flow = np.zeros(len(network.source))
        times: list[float | None] = [None] * len(self.trips)
        missing = 0.0
        for number, origin in enumerate(self.entries, 1):
            checkpoint(deadline, getattr(self, "check", None))
            if origin not in self.loads:
                self.loads[origin] = self._load_origin(origin)
            amounts, lost, reached = self.loads[origin]
            missing += lost
            for index, value in reached.items():
                times[index] = value
            indices = self.edges.edge_ids(amounts)
            np.add.at(flow, indices, np.fromiter(amounts.values(), dtype=float))
            progress = getattr(self, "progress", None)
            if progress is not None:
                progress({"stage": "loading_flows", "completed": number, "total": len(self.entries)})
        return flow, missing, times

    def _load_origin(
        self, origin: int
    ) -> tuple[dict[tuple[int, int], float], float, dict[int, float]]:
        return load_tree(self.trees[origin], self.entries[origin])


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
