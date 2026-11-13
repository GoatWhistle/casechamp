from dataclasses import replace
from time import monotonic

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.assignment import assign
from synthetic_traffic.incremental import evaluate_incremental, prepare_incremental
from synthetic_traffic.incremental_paths import GraphCache
from synthetic_traffic.model import Network, Trip


def network():
    return Network(
        source=np.array([0, 0, 1, 2, 1, 3, 4]),
        target=np.array([1, 2, 3, 3, 4, 4, 0]),
        free_hours=np.array([1.0, 1.2, 1.0, 1.0, 0.5, 1.0, 2.0]),
        capacity=np.array([10.0] * 7),
        length_km=np.ones(7),
        way_id=np.arange(7),
        raw_nodes=np.arange(5),
        lat=np.zeros(5),
        lon=np.zeros(5),
        shared=np.full(7, -1),
    )


@pytest.mark.parametrize("change", ["increase", "decrease", "close", "parallel", "new"])
def test_assignment_matches_full_recomputation(change):
    base = network()
    trips = [Trip(0, 4, 20.0), Trip(4, 3, 4.0), Trip(2, 1, 3.0)]
    baseline = prepare_incremental(base, trips, iterations=12)
    if change in {"increase", "decrease"}:
        hours = base.free_hours.copy()
        hours[0] *= 4 if change == "increase" else 0.1
        modified = replace(base, free_hours=hours)
    elif change == "close":
        selected = np.arange(1, 7)
        modified = replace(
            base,
            **{
                name: getattr(base, name)[selected]
                for name in [
                    "source",
                    "target",
                    "free_hours",
                    "capacity",
                    "length_km",
                    "way_id",
                    "shared",
                ]
            },
        )
    else:
        modified = replace(
            base,
            **{
                name: np.append(getattr(base, name), value)
                for name, value in {
                    "source": 0,
                    "target": 1 if change == "parallel" else 4,
                    "free_hours": 0.3,
                    "capacity": 10.0,
                    "length_km": 1.0,
                    "way_id": 999,
                    "shared": -1,
                }.items()
            },
        )
    actual = evaluate_incremental(baseline, modified, iterations=12)
    expected = assign(modified, trips, iterations=12)
    np.testing.assert_allclose(actual.flow, expected.flow)
    np.testing.assert_allclose(actual.hours, expected.hours)
    assert actual.od_hours == pytest.approx(expected.od_hours)
    assert actual.unserved_vehicles_per_hour == expected.unserved_vehicles_per_hour
    assert baseline.paths.repaired_origins == 0


def test_random_mixed_graph_changes_match_dijkstra():
    rng = np.random.default_rng(293)
    values = rng.uniform(0.1, 5, (18, 18))
    values[rng.random((18, 18)) < 0.8] = 0
    np.fill_diagonal(values, 0)
    cache = GraphCache(csr_matrix(values), range(18))
    for _ in range(30):
        for _ in range(8):
            u, v = rng.choice(18, 2, replace=False)
            values[u, v] = rng.choice([0.0, float(rng.uniform(0.1, 5))])
        graph = csr_matrix(values)
        cache.update_graph(graph)
        expected = dijkstra(graph, directed=True)
        for origin, tree in cache.trees.items():
            np.testing.assert_allclose(tree.distance, expected[origin])


def test_unaffected_origin_reuses_tree_and_loads():
    base = network()
    baseline = prepare_incremental(base, [Trip(0, 4, 1.0)])
    paths = baseline.paths.fork()
    paths.load(base)
    previous_load = paths.loads[0]
    hours = baseline.assignment.hours.copy()
    hours[5] += 1
    paths.update(base, hours)
    paths.load(base)
    assert paths.repaired_origins == 0
    assert paths.loads[0] is previous_load


def test_deadline_and_node_identity_are_checked():
    base = network()
    baseline = prepare_incremental(base, [Trip(0, 4, 1.0)])
    with pytest.raises(TimeoutError):
        evaluate_incremental(baseline, base, deadline=monotonic() - 1)
    with pytest.raises(ValueError, match="identities"):
        evaluate_incremental(baseline, replace(base, raw_nodes=base.raw_nodes[::-1]))


def test_baseline_checks_cancellation_between_assignment_iterations():
    checks = []

    def cancel():
        checks.append(True)
        if len(checks) == 5:
            raise RuntimeError("Cancelled")

    with pytest.raises(RuntimeError, match="Cancelled"):
        prepare_incremental(
            network(), [Trip(0, 4, 100.0)], iterations=20, tolerance=1e-10, check=cancel
        )
    assert len(checks) == 5


def test_graph_initialization_checks_cancellation_between_origins():
    checks = []

    def cancel():
        checks.append(True)
        if len(checks) == 2:
            raise RuntimeError("Cancelled")

    with pytest.raises(RuntimeError, match="Cancelled"):
        GraphCache(csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]])), [0, 1], check=cancel)
    assert len(checks) == 2


def test_candidate_progress_matches_assignment_without_mutating_baseline():
    base = network()
    baseline = prepare_incremental(base, [Trip(0, 4, 20)], iterations=12)
    saved_flow = baseline.assignment.flow.copy()
    events = []
    result = evaluate_incremental(baseline, base, iterations=12, progress=events.append)
    assert [row["iteration"] for row in events] == list(range(1, result.iterations + 1))
    assert events[-1]["relative_gap"] == result.relative_gap
    np.testing.assert_array_equal(saved_flow, baseline.assignment.flow)
