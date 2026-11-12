import json
from hashlib import sha256
from time import monotonic

import numpy as np
import pytest
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.assignment import assign
from synthetic_traffic.surrogate import (
    FEATURES,
    build_feature_context,
    features,
    load_surrogate,
)
from synthetic_traffic.training_scenarios import scenario


def test_endpoint_features_distinguish_routes_and_cache_exact_times():
    network, trips, projects = scenario(20261112)
    baseline = assign(network, trips, iterations=150, tolerance=1e-3)
    context = build_feature_context(network, baseline)
    connections = [p for p in projects if p["kind"] == "connection"]
    rows = np.array(
        [features(network, baseline, p, context=context) for p in connections]
    )
    assert rows.shape == (9, len(FEATURES))
    assert np.ptp(rows[:, 11]) > 0.001
    assert np.ptp(rows[:, 14]) > 0
    a, b = connections[0]["source_node"], connections[0]["target_node"]
    assert context.distance(a, b) == pytest.approx(
        dijkstra(context.graph, indices=a)[b]
    )
    count = len(context.distances)
    features(network, baseline, connections[0], context=context)
    assert len(context.distances) == count
    reverse = dict(connections[0], source_node=b, target_node=a)
    assert features(network, baseline, reverse, context=context) == pytest.approx(
        rows[0]
    )


def test_feature_context_checks_deadline_and_cancellation():
    network, trips, _ = scenario(1)
    baseline = assign(network, trips)
    with pytest.raises(TimeoutError):
        build_feature_context(network, baseline, deadline=monotonic() - 1)

    def stop():
        raise InterruptedError("cancelled")

    with pytest.raises(InterruptedError):
        build_feature_context(network, baseline, check=stop)


def test_old_feature_artifact_is_rejected_before_catboost_load(tmp_path):
    path = tmp_path / "old.cbm"
    path.write_bytes(b"old model")
    path.with_suffix(".json").write_text(
        json.dumps(
            {
                "artifact_sha256": sha256(path.read_bytes()).hexdigest(),
                "feature_schema": FEATURES[:10],
            }
        )
    )
    with pytest.raises(RuntimeError, match="schema"):
        load_surrogate(path)


def test_connection_package_combines_grounded_features_and_rejects_stale_times():
    network, trips, projects = scenario(4)
    baseline = assign(network, trips)
    context = build_feature_context(network, baseline)
    a, b = [p for p in projects if p["kind"] == "connection"][:2]
    package = features(
        network, baseline, {"kind": "package", "projects": [a, b]}, context=context
    )
    expected = (
        np.asarray(features(network, baseline, a, context=context))[10:]
        + np.asarray(features(network, baseline, b, context=context))[10:]
    )
    assert package[10:] == pytest.approx(expected)
    with pytest.raises(ValueError, match="travel time"):
        features(network, baseline, dict(a, free_travel_hours=999), context=context)
