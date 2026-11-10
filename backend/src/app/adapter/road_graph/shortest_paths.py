import shutil
import tempfile
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

MAX_WORKERS = 48
PARTS = ("data", "indices", "indptr")
_graphs: OrderedDict[str, tuple[Any, Any]] = OrderedDict()


def _attach(directory: str, shape: tuple[int, int]) -> tuple[Any, Any]:
    if directory not in _graphs:
        arrays = {part: np.load(Path(directory) / f"{part}.npy", mmap_mode="r") for part in PARTS}
        graph = csr_matrix(
            (arrays["data"], arrays["indices"], arrays["indptr"]), shape=shape, copy=False
        )
        targets = np.load(Path(directory) / "targets.npy", mmap_mode="r")
        _graphs[directory] = (graph, targets)
        while len(_graphs) > 2:
            _graphs.popitem(last=False)
    return _graphs[directory]


def _search(directory: str, shape: tuple[int, int], source: int, limit: float) -> Any:
    graph, targets = _attach(directory, shape)
    return dijkstra(graph, directed=True, indices=source, limit=limit)[targets]


class ShortestPaths:
    def __init__(self, workers: int = 1) -> None:
        if not 1 <= workers <= MAX_WORKERS:
            raise ValueError(f"Worker count must be between 1 and {MAX_WORKERS}")
        self.workers = workers
        self.pool: ProcessPoolExecutor | None = None
        self.lock = Lock()

    def distances(
        self,
        graph: Any,
        sources: Any,
        targets: Any,
        limit: float,
        progress: Callable[[int], None],
    ) -> Any:
        sources = np.asarray(sources, dtype=np.int64)
        targets = np.asarray(targets, dtype=np.int64)
        result = np.empty((len(sources), len(targets)))
        if self.workers == 1 or len(sources) < 2:
            for row, source in enumerate(sources):
                result[row] = dijkstra(graph, directed=True, indices=int(source), limit=limit)[
                    targets
                ]
                progress(row + 1)
            return result
        graph = csr_matrix(graph, dtype=np.float64)
        directory = tempfile.mkdtemp(prefix="road-graph-", dir=self.scratch(graph))
        try:
            for part in PARTS:
                np.save(Path(directory) / f"{part}.npy", getattr(graph, part))
            np.save(Path(directory) / "targets.npy", targets)
            pool = self.executor()
            futures: dict[Future[Any], int] = {
                pool.submit(_search, directory, graph.shape, int(source), limit): row
                for row, source in enumerate(sources)
            }
            try:
                for completed, future in enumerate(as_completed(futures), 1):
                    result[futures[future]] = future.result()
                    progress(completed)
            finally:
                for future in futures:
                    future.cancel()
        finally:
            shutil.rmtree(directory, ignore_errors=True)
        return result

    def scratch(self, graph: Any) -> str | None:
        shared = Path("/dev/shm")
        size = sum(getattr(graph, part).nbytes for part in PARTS)
        if shared.is_dir() and shutil.disk_usage(shared).free > size * 2:
            return str(shared)
        return None

    def executor(self) -> ProcessPoolExecutor:
        with self.lock:
            if self.pool is None:
                self.pool = ProcessPoolExecutor(
                    max_workers=self.workers, mp_context=get_context("spawn")
                )
            return self.pool

    def close(self) -> None:
        with self.lock:
            if self.pool is not None:
                self.pool.shutdown(wait=False, cancel_futures=True)
                self.pool = None
