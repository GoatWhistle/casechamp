from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from shutil import disk_usage
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.compiled_repair import warmup
from synthetic_traffic.incremental_paths import checkpoint
from synthetic_traffic.index_path_repair import changes, tree_impact, validated_delta
from synthetic_traffic.index_repair_workers import repair_markets


class DiskArray:
    def __init__(self, path: Path, overlay: Path | None = None, kind: str = "distance"):
        self.path, self.overlay, self.kind = path, overlay, kind

    def __getitem__(self, selected):
        base = np.load(self.path, mmap_mode="r")
        result = base[selected]
        if self.overlay is None:
            return result
        indices = np.load(self.overlay / "nodes.npy", mmap_mode="r")
        requested = np.asarray(
            np.arange(len(base))[selected] if isinstance(selected, slice) else selected
        )
        if requested.dtype == np.bool_:
            requested = np.flatnonzero(requested)
        requested = np.where(requested < 0, requested + len(base), requested)
        positions = np.searchsorted(indices, requested)
        present = positions < len(indices)
        if not len(indices):
            return result
        present &= indices[np.minimum(positions, len(indices) - 1)] == requested
        values = np.load(self.overlay / f"{self.kind}.npy", mmap_mode="r")
        if requested.ndim == 0:
            return values[int(positions)] if present else result
        result = np.array(result, copy=True)
        result[present] = values[positions[present]]
        return result

    def __array__(self, dtype=None, copy=None):
        result = np.array(np.load(self.path, mmap_mode="r"), dtype=dtype, copy=True)
        if self.overlay is not None:
            nodes = np.load(self.overlay / "nodes.npy", mmap_mode="r")
            result[nodes] = np.load(self.overlay / f"{self.kind}.npy", mmap_mode="r")
        return result


@dataclass
class DiskTree:
    directory: Path
    origin: int
    overlay: Path | None = None

    @property
    def distance(self):
        return DiskArray(self.directory / f"{self.origin}-distance.npy", self.overlay)

    @property
    def parent(self):
        return DiskArray(
            self.directory / f"{self.origin}-parent.npy", self.overlay, "parent"
        )

    def writable(self):
        distance = np.load(
            self.directory / f"{self.origin}-distance.npy", mmap_mode="c"
        )
        parent = np.load(self.directory / f"{self.origin}-parent.npy", mmap_mode="c")
        if self.overlay is not None:
            nodes = np.load(self.overlay / "nodes.npy", mmap_mode="r")
            distance[nodes] = np.load(self.overlay / "distance.npy", mmap_mode="r")
            parent[nodes] = np.load(self.overlay / "parent.npy", mmap_mode="r")
        return distance, parent


class DiskGraphCache:
    def __init__(
        self,
        graph,
        origins,
        cache_dir: str | Path,
        check: Callable[[], None] | None = None,
    ):
        checkpoint(None, check)
        warmup()
        self.graph = self.normalized(graph)
        digest = sha256(str(self.graph.shape).encode())
        for array in (self.graph.indptr, self.graph.indices, self.graph.data):
            digest.update(str((array.dtype.str, array.shape)).encode())
            digest.update(memoryview(array).cast("B"))
        self.directory = Path(cache_dir) / digest.hexdigest()
        self.directory.mkdir(parents=True, exist_ok=True)
        origins = list(dict.fromkeys(int(o) for o in origins))
        missing = [
            o
            for o in origins
            if not all(
                (self.directory / f"{o}-{kind}.npy").exists()
                for kind in ("distance", "parent")
            )
        ]
        required = len(missing) * (self.graph.shape[0] * 12 + 512)
        if disk_usage(self.directory).free < required * 1.1:
            raise OSError(
                f"Shortest-path baseline needs {required} bytes of free disk space"
            )
        self.trees = {}
        self._temporary = None
        self._parent = None
        self.repaired_origins = self.changed_nodes = 0
        self.considered_origins = self.skipped_origins = 0
        self.last_update_timings = {}
        for origin in origins:
            checkpoint(None, check)
            if origin in missing:
                distance, parent = dijkstra(
                    self.graph, directed=True, indices=origin, return_predecessors=True
                )
                with TemporaryDirectory(
                    prefix="building-", dir=self.directory
                ) as temporary:
                    for kind, array in (
                        ("distance", distance),
                        ("parent", parent.astype(np.int32)),
                    ):
                        path = Path(temporary) / f"{origin}-{kind}.npy"
                        np.save(path, array)
                        path.replace(self.directory / path.name)
                del distance, parent
            self.trees[origin] = DiskTree(self.directory, origin)
        checkpoint(None, check)

    @staticmethod
    def normalized(graph):
        result = graph.tocsr(copy=False)
        if not result.has_canonical_format:
            result = result.copy()
            result.sum_duplicates()
            result.sort_indices()
        return result

    def fork(self) -> "DiskGraphCache":
        result = object.__new__(DiskGraphCache)
        result.graph, result.directory = self.graph, self.directory
        result.trees = self.trees.copy()
        result._temporary = TemporaryDirectory(prefix="candidate-", dir=self.directory)
        result._parent = self
        result.repaired_origins = result.changed_nodes = 0
        result.considered_origins = result.skipped_origins = 0
        result.last_update_timings = {}
        return result

    def update_graph(
        self,
        graph,
        deadline: float | None = None,
        horizon: float = np.inf,
        delta=None,
        workers: int = 4,
    ) -> None:
        started = perf_counter()
        checkpoint(deadline)
        if np.isnan(horizon) or horizon < 0:
            raise ValueError("Index repair horizon must be nonnegative")
        graph = self.normalized(graph)
        if graph.shape != self.graph.shape:
            raise ValueError("Incremental graph must preserve node count")
        delta = (
            changes(self.graph, graph, deadline)
            if delta is None
            else validated_delta(self.graph, graph, delta)
        )
        self.last_update_timings = {
            "delta_seconds": perf_counter() - started,
            "delta_edges": len(delta[0]),
        }
        if not len(delta[0]):
            self.graph = graph
            self.last_update_timings["total_seconds"] = perf_counter() - started
            return
        if self._temporary is None:
            raise ValueError("Fork the immutable baseline before updating")
        phase = perf_counter()
        affected = []
        for origin, tree in self.trees.items():
            checkpoint(deadline)
            self.considered_origins += 1
            active, increase = tree_impact(tree, delta, horizon)
            if active:
                affected.append((origin, tree, increase))
            else:
                self.skipped_origins += 1
        self.last_update_timings["prefilter_seconds"] = perf_counter() - phase
        phase = perf_counter()
        reverse = (
            graph.transpose().tocsr()
            if any(increase for _, _, increase in affected)
            else None
        )
        self.last_update_timings["reverse_seconds"] = perf_counter() - phase
        self.last_update_timings["affected_origins"] = len(affected)
        phase = perf_counter()
        records, worker_count = repair_markets(
            affected,
            graph,
            reverse,
            delta,
            deadline,
            horizon,
            self._temporary.name,
            workers,
        )
        checkpoint(deadline)
        updates = {
            origin: DiskTree(self.directory, origin, directory)
            for origin, directory, _ in records
        }
        self.trees.update(updates)
        self.repaired_origins += len(records)
        self.changed_nodes += sum(count for _, _, count in records)
        self.last_update_timings["workers"] = worker_count
        self.graph = graph
        self.last_update_timings["repair_and_overlay_seconds"] = perf_counter() - phase
        self.last_update_timings["total_seconds"] = perf_counter() - started

    def close(self) -> None:
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None
