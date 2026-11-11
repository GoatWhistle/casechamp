from dataclasses import replace
from unittest.mock import Mock

import pytest

from app.domain.errors import InvalidQuery
from app.usecase.calculation_tables import CalculationTables
from app.usecase.road_graph import RoadChange, RoadJob, RoadResult
from app.usecase.road_stress import StressJob


def test_comparison_keeps_each_scenario_and_its_exact_values_separate() -> None:
    roads, stress = Mock(), Mock()
    stress.get.side_effect = lambda key: StressJob(
        key, "v", [10] if key == "single" else [10, 11], status="completed"
    )
    stress.geometry.side_effect = lambda key: Mock(
        names=["М-10"] if key == "single" else ["М-10", "М-11", "Улица"]
    )
    base = RoadJob(
        "index",
        "53",
        "Новгородская область",
        "road",
        [RoadChange(10, 0)],
        "completed",
        360,
        360,
        "v",
        RoadResult(84.144, 70.3, -13.844, -16.45, 1000, 10, 2, 1, 1),
    )
    assert base.result is not None
    base_result = base.result
    roads.closure_jobs.side_effect = lambda ways, version: [
        base
        if ways == [10]
        else replace(
            base, id="joint-index", result=replace(base_result, after=54.96, delta=-29.184)
        )
    ]
    tables = CalculationTables(roads, stress).build([], ["single", "joint"])
    assert [table.caption for table in tables] == ["М-10", "М-10, М-11"]
    assert [table.rows[0]["after"] for table in tables] == [70.3, 54.96]
    assert all(len(table.columns) == 4 for table in tables)
    assert tables[0].rows[0]["before"] == 84.144
    assert all(isinstance(table.rows[0]["after"], float) for table in tables)


def test_incomplete_calculation_does_not_create_a_final_table() -> None:
    stress = Mock()
    stress.get.return_value = StressJob("running", "v", [10], status="running")
    with pytest.raises(InvalidQuery, match="Wait"):
        CalculationTables(None, stress).build([], ["running"])


def test_saved_regional_jobs_group_under_their_actual_road_names() -> None:
    roads = Mock()
    roads.geometry.return_value.names = ["М-10", "Улица"]
    base = RoadJob(
        "a",
        "53",
        "Новгородская область",
        "road",
        [RoadChange(10, 0)],
        "completed",
        360,
        360,
        "v",
        RoadResult(84, 70, -14, -16.7, 1000, 10, 2, 1, 1),
    )
    roads.job.side_effect = lambda key: (
        base if key == "a" else replace(base, id="b", region="Тверская область", region_id="69")
    )
    tables = CalculationTables(roads, None).build(["a", "b"], [])
    assert len(tables) == 1
    assert tables[0].caption == "М-10"
    assert tables[0].total == 2
    assert [row["name"] for row in tables[0].rows] == ["Новгородская область", "Тверская область"]
