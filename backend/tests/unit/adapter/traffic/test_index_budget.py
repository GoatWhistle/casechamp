from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.search import SearchReport

from app.adapter.traffic import development
from app.adapter.traffic.indices import TrafficIndices
from app.usecase.traffic import TrafficIndexValue, TrafficJob, TrafficScope


def test_index_slice_is_sixty_seconds_but_never_exceeds_overall_deadline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network = Network(
        source=np.array([0]),
        target=np.array([1]),
        free_hours=np.ones(1),
        capacity=np.full(1, 100.0),
        length_km=np.ones(1),
        way_id=np.array([10]),
        raw_nodes=np.arange(2),
        lat=np.zeros(2),
        lon=np.arange(2, dtype=float),
        shared=np.array([-1]),
    )
    trips = [Trip(0, 1, 1.0)]
    baseline = prepare_incremental(network, trips)
    values = [TrafficIndexValue("R", 10, 100, 1, 100)]
    clock, deadlines = [0.0], []

    def evaluate(changed: Network, hours: Any, deadline: float) -> Any:
        deadlines.append(deadline)
        return values

    fake_cache = SimpleNamespace(baseline=values, evaluate=evaluate)
    indices = cast(
        TrafficIndices,
        SimpleNamespace(
            revision=lambda _: "r", data=SimpleNamespace(revision="r"), regions=lambda *args: ["R"]
        ),
    )

    def search(*args: Any, **kwargs: Any) -> SearchReport:
        assert kwargs["deadline"] == 300
        assert kwargs["seconds"] == 300
        changed = replace(network, capacity=network.capacity.copy())
        assert kwargs["score"](changed, baseline.assignment) == 10
        clock[0] = 295
        assert kwargs["score"](changed, baseline.assignment) == 10
        return SearchReport([], 2, 295, "exhausted", "test", kwargs["deadline"], 2, 0)

    monkeypatch.setattr(development, "monotonic", lambda: clock[0])
    monkeypatch.setattr(development, "IndexDelta", lambda *args: fake_cache)
    monkeypatch.setattr(development, "index_route_targets", lambda *args: [])
    monkeypatch.setattr(development, "resolve_hypotheses", lambda *args: [])
    monkeypatch.setattr(development, "generate_candidates", lambda *args, **kwargs: {})
    monkeypatch.setattr(development, "search_projects", search)
    development.develop(
        TrafficJob("traffic-budget", TrafficScope()),
        tmp_path,
        network,
        trips,
        [],
        baseline,
        indices,
        lambda _: None,
        lambda: None,
    )
    assert deadlines == [60, 300]
