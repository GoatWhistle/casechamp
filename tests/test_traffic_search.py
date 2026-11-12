import multiprocessing as mp
import time
from pathlib import Path

import pytest
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.search import search_projects
from synthetic_traffic.surrogate import ARTIFACT, FEATURES, features, load_surrogate
from synthetic_traffic.training import scenario


def test_missing_mandatory_model_fails_explicitly(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Required CatBoost"):
        load_surrogate(tmp_path / "absent.cbm")


def test_search_verifies_broad_pool_and_cleans_processes() -> None:
    network, trips, candidates = scenario(20261112)
    baseline = prepare_incremental(network, trips, iterations=150)
    previous = {process.pid for process in mp.active_children()}
    report = search_projects(
        network,
        trips,
        candidates[:8],
        baseline,
        workers=2,
        seconds=20,
        iterations=150,
        package_limit=0,
        limit=8,
    )
    assert report.evaluated == 8
    assert report.results
    assert all(result.index_delta > 0 for result in report.results)
    assert [r.index_delta for r in report.results] == sorted(
        [r.index_delta for r in report.results], reverse=True
    )
    assert {process.pid for process in mp.active_children()} == previous


def test_deadline_and_cancellation_leave_no_children() -> None:
    network, trips, candidates = scenario(2)
    baseline = prepare_incremental(network, trips, iterations=150)
    before = {process.pid for process in mp.active_children()}
    start = time.monotonic()
    report = search_projects(
        network,
        trips,
        candidates,
        baseline,
        workers=2,
        seconds=0.1,
        cancelled=lambda: True,
    )
    assert report.stop_reason == "cancelled"
    assert time.monotonic() - start < 2
    assert {process.pid for process in mp.active_children()} == before


def test_model_is_trained_and_schema_matches() -> None:
    model = load_surrogate(ARTIFACT)
    assert model.tree_count_ > 0


def test_expired_deadline_skips_score_and_optimization() -> None:
    network, trips, candidates = scenario(2)
    baseline = prepare_incremental(network, trips, iterations=150)
    calls = []
    report = search_projects(
        network,
        trips,
        candidates,
        baseline,
        deadline=time.monotonic() - 1,
        score=lambda n, a: calls.append(n) or 0.0,
    )
    assert report.stop_reason == "deadline"
    assert report.evaluated == 0
    assert calls == []


def test_candidate_timeout_does_not_consume_entire_search() -> None:
    network, trips, candidates = scenario(20261112)
    baseline = prepare_incremental(network, trips, iterations=150)
    calls = []

    def score(changed, assignment):
        calls.append(changed)
        if len(calls) == 2:
            raise TimeoutError("Candidate verification slice exhausted")
        return 0.0 if changed is network else 1.0

    report = search_projects(
        network,
        trips,
        candidates[:8],
        baseline,
        workers=2,
        seconds=20,
        iterations=150,
        package_limit=0,
        score=score,
    )
    assert report.evaluated == 8
    assert report.rejected >= 1
    assert report.verified >= 1
    assert report.results
    assert report.stop_reason == "exhausted"


def test_surrogate_rejects_speed_projects_and_uses_lane_features() -> None:
    network, trips, _ = scenario(2)
    baseline = prepare_incremental(network, trips, iterations=150)
    project = {"kind": "speed", "way_ids": [1], "factor": 1.3}
    assert "factor" not in FEATURES
    assert "extra_lanes" in FEATURES
    for value in [project, {"kind": "package", "projects": [project]}]:
        with pytest.raises(ValueError, match="Unsupported project kind"):
            features(network, baseline.assignment, value)


def test_five_minute_default_and_upper_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    network, trips, _ = scenario(20261112)
    baseline = prepare_incremental(network, trips, iterations=150)
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    report = search_projects(network, trips, [], baseline)
    assert report.deadline == 1300
    assert report.stop_reason == "exhausted"
    with pytest.raises(ValueError, match="0..300 seconds"):
        search_projects(network, trips, [], baseline, seconds=301)


def test_exact_duplicates_are_verified_once_with_merged_sources_and_observation_callback():
    network, trips, candidates = scenario(20261112)
    baseline = prepare_incremental(network, trips, iterations=150)
    original = {**candidates[0], "target_origin": "index_route"}
    duplicate = {**candidates[0], "target_origin": "agent_hypothesis"}
    seen = []
    report = search_projects(
        network,
        trips,
        [original, duplicate],
        baseline,
        workers=2,
        seconds=20,
        package_limit=0,
        score=lambda changed, after: 0.0 if changed is network else 1.0,
        on_evaluated=lambda project, after, value, before: seen.append(
            (project, value, before)
        ),
    )
    assert report.evaluated == report.verified == len(seen) == 1
    assert report.deduplicated == 1 and report.distinct_projects == 1
    assert {row["target_origin"] for row in seen[0][0]["source_provenance"]} == {
        "index_route",
        "agent_hypothesis",
    }


def test_nonfinite_objective_results_are_not_observed_or_verified():
    network, trips, candidates = scenario(20261112)
    baseline = prepare_incremental(network, trips, iterations=150)
    seen = []
    report = search_projects(
        network,
        trips,
        candidates[:2],
        baseline,
        workers=2,
        seconds=20,
        package_limit=0,
        score=lambda changed, after: 0.0 if changed is network else -float("inf"),
        on_evaluated=lambda *args: seen.append(args),
    )
    assert report.verified == 0 and report.rejected == report.evaluated == 2
    assert not seen and not report.results
