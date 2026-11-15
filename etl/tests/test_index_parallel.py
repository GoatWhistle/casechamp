from pathlib import Path
from threading import Event
from threading import enumerate as live_threads
from time import monotonic, sleep

import numpy as np
import pytest
import synthetic_traffic.index_repair_workers as workers
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.index_paths import DiskGraphCache


def graph_values():
    rng = np.random.default_rng(4539)
    values = rng.uniform(0.2, 5, (40, 40))
    values[rng.random((40, 40)) < 0.9] = 0
    np.fill_diagonal(values, 0)
    return values


def assert_no_repair_threads():
    assert not [
        thread for thread in live_threads() if thread.name.startswith("plexus-index")
    ]


def test_four_workers_match_serial_and_full_dijkstra(tmp_path, monkeypatch):
    monkeypatch.setattr(workers.os, "cpu_count", lambda: 4)
    values = graph_values()
    original = csr_matrix(values)
    baseline = DiskGraphCache(original, range(12), tmp_path)
    serial, parallel = baseline.fork(), baseline.fork()
    rng = np.random.default_rng(614)
    try:
        for _ in range(12):
            for _ in range(8):
                a, b = rng.choice(40, 2, replace=False)
                values[a, b] = rng.choice([0.0, float(rng.uniform(0.05, 4))])
            graph = csr_matrix(values)
            serial.update_graph(graph, monotonic() + 10, workers=1)
            parallel.update_graph(graph, monotonic() + 10, workers=4)
            expected = dijkstra(graph, directed=True, indices=list(range(12)))
            for origin in range(12):
                np.testing.assert_allclose(
                    np.asarray(serial.trees[origin].distance), expected[origin]
                )
                np.testing.assert_allclose(
                    np.asarray(parallel.trees[origin].distance), expected[origin]
                )
            assert serial.changed_nodes == parallel.changed_nodes
            assert serial.repaired_origins == parallel.repaired_origins
        for origin in range(12):
            np.testing.assert_allclose(
                np.asarray(baseline.trees[origin].distance),
                dijkstra(original, indices=origin),
            )
    finally:
        serial.close()
        parallel.close()
    assert_no_repair_threads()


@pytest.mark.parametrize("failure", [TimeoutError, ValueError])
def test_failed_batch_has_no_partial_publish_or_lingering_threads(
    tmp_path, monkeypatch, failure
):
    graph = csr_matrix(np.array([[0.0, 2.0, 9.0], [2.0, 0.0, 2.0], [9.0, 2.0, 0.0]]))
    baseline = DiskGraphCache(graph, [0, 1, 2], tmp_path)
    candidate = baseline.fork()
    before = candidate.trees.copy()
    changed = csr_matrix(np.array([[0.0, 2.0, 0.1], [2.0, 0.0, 2.0], [0.1, 2.0, 0.0]]))
    entered = Event()
    real = workers.repair
    calls = []

    def fail_or_finish(*args, **kwargs):
        calls.append(True)
        if len(calls) == 1:
            entered.wait(timeout=2)
            raise failure("Injected batch failure")
        entered.set()
        sleep(0.02)
        return real(*args, **kwargs)

    monkeypatch.setattr(workers.os, "cpu_count", lambda: 4)
    monkeypatch.setattr(workers, "repair", fail_or_finish)
    try:
        with pytest.raises(failure, match="Injected batch failure"):
            candidate.update_graph(changed, monotonic() + 5, workers=4)
        assert candidate.graph is baseline.graph
        assert candidate.repaired_origins == candidate.changed_nodes == 0
        assert all(candidate.trees[node] is tree for node, tree in before.items())
        assert not list(Path(candidate._temporary.name).glob("update-*"))
        assert_no_repair_threads()
    finally:
        candidate.close()


def test_deadline_cancels_batch_before_publication_and_waits_for_all_workers(tmp_path):
    values = graph_values()
    baseline = DiskGraphCache(csr_matrix(values), range(10), tmp_path)
    candidate = baseline.fork()
    try:
        with pytest.raises(TimeoutError):
            candidate.update_graph(
                csr_matrix(values), deadline=monotonic() - 1, workers=4
            )
        assert candidate.repaired_origins == 0
        assert_no_repair_threads()
    finally:
        candidate.close()


def test_expiring_running_workers_are_joined_before_return(tmp_path, monkeypatch):
    graph = csr_matrix(np.array([[0.0, 2.0, 9.0], [2.0, 0.0, 2.0], [9.0, 2.0, 0.0]]))
    baseline = DiskGraphCache(graph, [0, 1, 2], tmp_path)
    candidate = baseline.fork()
    changed = csr_matrix(np.array([[0.0, 2.0, 0.1], [2.0, 0.0, 2.0], [0.1, 2.0, 0.0]]))
    real, calls = workers.repair, []

    def slow(*args, **kwargs):
        calls.append(True)
        sleep(0.15)
        return real(*args, **kwargs)

    monkeypatch.setattr(workers, "repair", slow)
    try:
        with pytest.raises(TimeoutError):
            candidate.update_graph(changed, monotonic() + 0.1, workers=4)
        assert calls
        assert candidate.repaired_origins == candidate.changed_nodes == 0
        assert not list(Path(candidate._temporary.name).glob("update-*"))
        assert_no_repair_threads()
    finally:
        candidate.close()
