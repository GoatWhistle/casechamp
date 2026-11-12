import os
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from threading import Event

import numpy as np
from synthetic_traffic.compiled_repair import repair
from synthetic_traffic.incremental_paths import checkpoint


def _check(deadline, cancelled):
    checkpoint(deadline)
    if cancelled.is_set():
        raise CancelledError("Index repair batch cancelled")


def _one(item, graph, reverse, delta, deadline, horizon, directory, cancelled):
    origin, tree, _ = item
    _check(deadline, cancelled)
    distance, parent = tree.writable()
    try:
        touched = repair(graph, reverse, distance, parent, delta, deadline, horizon)
        _check(deadline, cancelled)
        if not len(touched):
            return None
        count = len(touched)
        if tree.overlay is not None:
            touched = np.union1d(
                touched, np.load(tree.overlay / "nodes.npy", mmap_mode="r")
            )
        output = directory / str(origin)
        output.mkdir()
        for kind, values in (
            ("nodes", touched),
            ("distance", distance[touched]),
            ("parent", parent[touched]),
        ):
            _check(deadline, cancelled)
            np.save(output / f"{kind}.npy", values)
        _check(deadline, cancelled)
        return origin, output, count
    finally:
        distance._mmap.close()
        parent._mmap.close()


def repair_markets(
    affected, graph, reverse, delta, deadline, horizon, directory, workers=4
):
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError("Index repair requires a positive integer worker count")
    count = min(4, workers, os.cpu_count() or 1, len(affected))
    if not count:
        return [], 0
    stage = Path(mkdtemp(prefix="update-", dir=directory))
    cancelled, committed = Event(), False
    try:
        args = graph, reverse, delta, deadline, horizon, stage, cancelled
        if count == 1:
            records = [_one(item, *args) for item in affected]
        else:
            pool = ThreadPoolExecutor(
                max_workers=count, thread_name_prefix="plexus-index"
            )
            futures = []
            try:
                futures = [pool.submit(_one, item, *args) for item in affected]
                records = []
                for future in as_completed(futures):
                    checkpoint(deadline)
                    records.append(future.result())
            finally:
                cancelled.set()
                for future in futures:
                    future.cancel()
                pool.shutdown(wait=True, cancel_futures=True)
        checkpoint(deadline)
        committed = True
        return [record for record in records if record is not None], count
    finally:
        if not committed:
            rmtree(stage)
