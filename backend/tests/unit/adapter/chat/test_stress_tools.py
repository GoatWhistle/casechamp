import json
from dataclasses import replace
from unittest.mock import Mock

import pytest
from pydantic_ai import ModelRetry

from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.scenario_requests import SelectionClosure
from app.adapter.chat.stress_tools import StressTools
from app.adapter.road_stress.jobs import StressJobs
from app.usecase.road_graph import RoadChange, RoadJob
from app.usecase.road_stress import StressImpact, StressJob, StressPoint, StressTotals


def engine_for(job: StressJob, totals: StressTotals | None = None) -> Mock:
    engine = Mock()
    engine.get.return_value = job
    engine.submit.return_value = job
    engine.store.totals.return_value = totals
    engine.store.consequences.return_value = None
    engine.consequences.side_effect = lambda key, region: engine.store.consequences(key, region)
    engine.summary.side_effect = lambda key, region="": StressJobs.summary(engine, key, region)
    engine.impacts.return_value = []
    engine.geometry.return_value.names = []
    return engine


def test_agent_uses_selected_roads_and_preserves_parent() -> None:
    engine = engine_for(StressJob("new", "v", [1, 2], "parent"))
    context = Mock()
    context.deps.context.road_way_ids = (2,)
    context.deps.pending = []
    result = json.loads(StressTools(engine, None).stress_test_roads(context, [], [], "parent"))
    engine.submit.assert_called_once_with([2], "parent")
    assert result["summary"]["parent_id"] == "parent"
    assert result["summary"]["totals"] is None
    engine.store.totals.assert_not_called()
    assert context.deps.pending[0].stress_test.id == "new"


def test_inspection_returns_real_impacts_and_live_card() -> None:
    engine = engine_for(StressJob("id", "v", [1], status="completed"),
                        StressTotals(10, 100, 2, 20, 65, 1))
    point = StressPoint("p", "Village", "r", 20, 4, 0, 30, 50)
    engine.impacts.return_value = [StressImpact(point, 180, True, 0, "Market")]
    context = Mock()
    context.deps.pending = []
    result = json.loads(StressTools(engine, None).inspect_road_stress_test(context, "id", "r"))
    engine.impacts.assert_called_once_with("id", "r", 0, 5)
    engine.store.totals.assert_called_once_with("id", "r")
    assert result["summary"]["totals"]["isolated_population"] == 20
    assert result["points"][0]["id"] == "p"
    assert "markets" not in result["points"][0]
    assert "way_ids" not in result["summary"]
    assert context.deps.pending[0].type == "stress_test"


def test_default_closure_uses_national_impact_without_unrelated_map_roads() -> None:
    engine = engine_for(StressJob("id", "v", [1], status="completed"),
                        StressTotals(0, 0, 0, 0, 0, 0))
    corridors = Mock()
    corridors.recent_connectivity.return_value = "[]"
    corridors.get.return_value.regions = []
    corridors.get.return_value.way_ids = [1]
    context = Mock()
    context.deps.context.road_way_ids = [99]
    context.deps.pending = []
    result = json.loads(NetworkScenarios(None, corridors, None, engine).calculate_scenario(
        context, SelectionClosure("close_selection", ["selection"])
    ))
    engine.submit.assert_called_once_with([1], None)
    corridors.close.assert_not_called()
    assert result["summary"]["totals"]["affected_points"] == 0
    assert context.deps.pending[0].stress_test.id == "id"


def test_saved_hansen_closure_transfers_exact_ways_without_viewport_substitution() -> None:
    engine = engine_for(StressJob("impact", "v", [11, 12], status="completed"),
                        StressTotals(0, 0, 0, 0, 0, 0))
    roads = Mock()
    roads.closure_jobs.return_value = []
    roads.submit_closure.return_value = []
    roads.model_info.return_value.version = "v"
    roads.job.return_value = RoadJob("legacy", "r", "Region", "road",
        [RoadChange(12, 0), RoadChange(11, 0)], "completed", 360, 360, "v")
    context = Mock()
    context.deps.context.road_way_ids = [99]
    context.deps.pending = []
    result = json.loads(StressTools(engine, None, roads).stress_test_roads(
        context, [], [], source_calculation_id="legacy",
    ))
    engine.submit.assert_called_once_with([11, 12], None)
    assert result["source_calculation_id"] == "legacy"
    assert result["summary"]["id"] == "impact"
    roads.job.return_value = replace(roads.job.return_value, changes=[RoadChange(11, 1.2)])
    with pytest.raises(ModelRetry, match="without speed edits"):
        StressTools(engine, None, roads).stress_test_roads(context, [], [], source_calculation_id="legacy")
    assert engine.submit.call_count == 1
    roads.job.return_value = replace(roads.job.return_value, version="old")
    with pytest.raises(ModelRetry, match="different graph version"):
        StressTools(engine, None, roads).stress_test_roads(context, [], [], source_calculation_id="legacy")
