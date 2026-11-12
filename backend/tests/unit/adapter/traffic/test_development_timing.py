import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.search import SearchReport

from app.adapter.traffic import development
from app.usecase.traffic import TrafficJob, TrafficScope


class Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class Objective:
    def __call__(self, *args: Any) -> float:
        return -1.0

    def metrics(self, *args: Any) -> dict[str, object]:
        return {"objective": "congestion"}


def inputs() -> tuple[Network, list[Trip]]:
    network = Network(
        source=np.array([0]),
        target=np.array([1]),
        free_hours=np.array([1.0]),
        capacity=np.array([100.0]),
        length_km=np.array([1.0]),
        way_id=np.array([10]),
        raw_nodes=np.array([0, 1]),
        lat=np.zeros(2),
        lon=np.array([0.0, 1.0]),
        shared=np.array([-1]),
    )
    return network, [Trip(0, 1, 1.0)]


def test_verification_receives_five_minutes_after_generation_and_preparation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network, trips = inputs()
    baseline = prepare_incremental(network, trips)
    clock = Clock()
    updates: list[TrafficJob] = []
    resolved: list[dict[str, object]] = [
        {"source_node": 0, "target_node": 1, "reason": "hypothesis"}
    ]
    scope = TrafficScope(objective="congestion")

    def prepare(*args: Any) -> Objective:
        clock.now += 30
        return Objective()

    def resolve(hypotheses: Any, path: Path, graph: Network) -> list[dict[str, object]]:
        assert hypotheses is scope.hypotheses
        assert path == tmp_path and graph is network
        return resolved

    def generate(*args: Any, **kwargs: Any) -> dict[str, object]:
        assert kwargs["deadline"] == clock.now + 120
        assert kwargs["trips"] is trips and kwargs["zones"] == []
        assert kwargs["hypotheses"] is resolved
        kwargs["check"]()
        clock.now += 90
        return {"existing_corridor_projects": []}

    def search(*args: Any, **kwargs: Any) -> SearchReport:
        assert clock.now == 220
        assert kwargs["deadline"] - clock.now == 300
        assert kwargs["seconds"] == 300
        kwargs["on_evaluated"](
            {"kind": "closure", "way_ids": [10]}, baseline.assignment, -1.2, -1.0
        )
        kwargs["on_evaluated"](
            {"kind": "capacity", "way_ids": [10], "extra_lanes": 1},
            baseline.assignment, -0.8, -1.0,
        )
        clock.now += 298
        return SearchReport([], 4, 298, "deadline", "test", kwargs["deadline"], 2, 2)

    monkeypatch.setattr(development, "monotonic", clock)
    monkeypatch.setattr(development, "build_objective", prepare)
    monkeypatch.setattr(development, "resolve_hypotheses", resolve)
    monkeypatch.setattr(development, "generate_candidates", generate)
    monkeypatch.setattr(development, "search_projects", search)
    result = development.develop(
        TrafficJob("traffic-timing", scope),
        tmp_path,
        network,
        trips,
        [],
        baseline,
        None,
        updates.append,
        lambda: None,
    )
    evidence = json.loads(result.provenance)
    observations = evidence["verified_observations"]
    assert len(observations) == 2
    assert observations[0]["gain"] == pytest.approx(-0.2)
    assert observations[1]["gain"] == pytest.approx(0.2)
    assert observations[0]["objective"] == "congestion"
    assert observations[0]["metric"] == "negative_vehicle_delay_hours"
    assert observations[0]["project"]["way_ids"] == [10]
    assert evidence["generation_seconds"] == 90
    assert evidence["generation_limit_seconds"] == 120
    assert evidence["verification_seconds"] == evidence["search_seconds"] == 298
    assert evidence["verification_limit_seconds"] == evidence["search_limit_seconds"] == 300
    assert evidence["total_development_seconds"] == 418
    assert [(row.stage, row.total) for row in updates] == [("candidates", 120), ("comparing", 300)]


@pytest.mark.parametrize("inside", [False, True])
def test_generation_cancellation_never_starts_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    inside: bool,
) -> None:
    network, trips = inputs()
    baseline = prepare_incremental(network, trips)
    checkpoints: list[bool] = []
    updates: list[TrafficJob] = []

    def check() -> None:
        checkpoints.append(True)
        if len(checkpoints) == 2:
            raise RuntimeError("Cancelled")

    def generate(*args: Any, **kwargs: Any) -> dict[str, object]:
        if inside:
            kwargs["check"]()
        return {"existing_corridor_projects": []}

    def forbidden_search(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Verification started after cancellation")

    monkeypatch.setattr(development, "build_objective", lambda *args: Objective())
    monkeypatch.setattr(development, "resolve_hypotheses", lambda *args: [])
    monkeypatch.setattr(development, "generate_candidates", generate)
    monkeypatch.setattr(development, "search_projects", forbidden_search)
    with pytest.raises(RuntimeError, match="Cancelled"):
        development.develop(
            TrafficJob("traffic-cancel", TrafficScope(objective="congestion")),
            tmp_path,
            network,
            trips,
            [],
            baseline,
            None,
            updates.append,
            check,
        )
    assert [row.stage for row in updates] == ["candidates"]
