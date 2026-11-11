from pathlib import Path
from typing import Any

import pytest
from tests.unit.adapter.road_graph.test_routing import Snapshot

from app.adapter.road_graph.appraisal import AppraisalRouting
from app.adapter.road_graph.baselines import BaselineCache
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.full_calculation import FullCalculation
from app.adapter.road_graph.routing import GraphRouting
from app.domain.appraisal_inputs import DemandScenario, PassengerFlow, ProjectAssumptions
from app.usecase.graph_snapshot import GraphParameters, GraphQuery
from app.usecase.road_graph import RoadChange, RoadJob
from app.usecase.transport_links import LinkChange


def test_real_route_closure_produces_negative_economic_effect(tmp_path: Path) -> None:
    assumptions = ProjectAssumptions(
        [PassengerFlow("origin", "market", 100, 200, "Test assumption")],
        [DemandScenario("low", 0.5, 1), DemandScenario("base", 1, 1), DemandScenario("high", 2, 1)],
        0,
        0,
        1,
        0,
        2026,
        "No construction cost",
    )
    appraisal = AppraisalRouting(assumptions)
    routing = GraphRouting(GraphData(tmp_path, Snapshot()))
    routing.calculate("region", "road", [], lambda _: None, on_times=appraisal.before)
    routing.calculate(
        "region", "road", [RoadChange(101, 0)], lambda _: None, on_times=appraisal.after
    )
    report = appraisal.result()
    assert report.travel[0].before_hours == pytest.approx(2)
    assert report.travel[0].after_hours == pytest.approx(5)
    assert report.scenarios[1].annual_gross_rub == -60000


def test_cached_link_change_keeps_passenger_time_evidence(tmp_path: Path) -> None:
    class LinkedSnapshot(Snapshot):
        def read(
            self, query: GraphQuery, parameters: GraphParameters | None = None
        ) -> list[tuple[Any, ...]]:
            if query == "cities":
                return [("origin_market", 0, 0.0, 100), ("market", 2, 0.0, 100)]
            if query == "expected":
                return [(150.0,)]
            return super().read(query, parameters)

    project = ProjectAssumptions(
        [PassengerFlow("origin", "market", 100, 200, "Test assumption")],
        [DemandScenario("low", 0.5, 1), DemandScenario("base", 1, 1), DemandScenario("high", 2, 1)],
        0,
        0,
        1,
        0,
        2026,
        "No construction cost",
    )
    data = GraphData(tmp_path, LinkedSnapshot())
    routing = GraphRouting(data)
    calculation = FullCalculation(data, routing, BaselineCache(tmp_path, "[]"), {})
    job = RoadJob(
        "test",
        "region",
        "region",
        "road",
        [],
        "queued",
        0,
        360,
        "test",
        links=[LinkChange("add", "intercity", "rail", "origin_market", "market", 0.1)],
        appraisal_assumptions=project,
    )
    for _ in range(2):
        appraisal = AppraisalRouting(project)
        result = calculation.calculate(job, "region", lambda _: None, appraisal)
        report = appraisal.result()
        assert result.after > result.before
        assert report.travel[0].before_hours == pytest.approx(2)
        assert report.travel[0].after_hours == pytest.approx(1.1)
        assert report.scenarios[1].annual_gross_rub == pytest.approx(18000, abs=0.01)
