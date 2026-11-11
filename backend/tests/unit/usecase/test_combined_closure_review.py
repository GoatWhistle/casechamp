import json
from dataclasses import replace
from threading import Lock
from unittest.mock import Mock

import pytest

from app.domain.errors import InvalidQuery
from app.usecase.chat_calculation_review import CalculationReview, CalculationReviews
from app.usecase.closure_matching import matching_closure_jobs
from app.usecase.road_graph import RoadChange, RoadGraph, RoadJob, RoadResult
from app.usecase.road_stress import StressJob, StressSummary


def index_job(key: str = "index") -> RoadJob:
    return RoadJob(
        key,
        "50",
        "Московская область",
        "road",
        [RoadChange(10, 0)],
        "completed",
        360,
        360,
        "v",
        RoadResult(100, 98, -2, -2, 1000, 10, 1, 1, 1),
    )


def test_closure_matching_excludes_other_scenarios_and_keeps_completed_result() -> None:
    engine = Mock()
    engine.lock = Lock()
    base = index_job()
    engine.jobs = {
        j.id: j
        for j in [
            base,
            replace(base, id="old", version="old"),
            replace(base, id="speed", changes=[RoadChange(10, 1.2)]),
            replace(base, id="joint", changes=[RoadChange(10, 0), RoadChange(11, 0)]),
            replace(base, id="profile", changes=[RoadChange(10, 0, lanes_total=4)]),
            replace(base, id="failed", status="failed"),
            replace(base, id="other-region", region_id="78"),
        ]
    }
    assert [j.id for j in matching_closure_jobs(list(engine.jobs.values()), [10], "v")] == [
        "index",
        "other-region",
    ]


def test_closure_submits_large_selection_once_and_reuses_matching_result() -> None:
    engine, atlas = Mock(), Mock()
    engine.metadata.version = "v"
    region = Mock()
    region.id, region.name = "50", "Московская область"
    atlas.regions.return_value = [region]
    engine.recent.return_value = []
    roads = RoadGraph(engine, atlas)
    ways = list(range(1, 715))
    roads.submit_closure(ways, ["50", "50"], "v")
    assert len(engine.submit.call_args.args[3]) == 714
    engine.submit.assert_called_once()
    engine.reset_mock()
    engine.recent.return_value = [index_job()]
    assert roads.submit_closure([10], ["50"], "v")[0].id == "index"
    engine.submit.assert_not_called()
    with pytest.raises(InvalidQuery, match="different graph"):
        roads.submit_closure([10], ["50"], "old")


def test_combined_review_waits_for_index_then_supplies_it_once_with_consequences() -> None:
    roads, stress = Mock(), Mock()
    stress.get.return_value = StressJob("stress", "v", [10], status="completed")
    stress.geometry.return_value.names = ["М-10"]
    stress.summary.return_value = StressSummary(
        "stress", "v", "completed", "completed", 1, None, "", None, 100, 0, 0, 180, 180
    )
    roads.closure_jobs.return_value = [replace(index_job(), status="running", result=None)]
    review = CalculationReviews(roads, stress)
    request = CalculationReview(("index",), ("stress",))
    with pytest.raises(InvalidQuery, match="still running"):
        review.prompt(request)
    roads.closure_jobs.return_value = [index_job()]
    payload = json.loads(review.prompt(request).split("Saved results: ", 1)[1])
    assert len(payload) == 1
    assert payload[0]["indices"][0]["result"]["before"] == 100
    assert payload[0]["indices"][0]["result"]["after"] == 98
    assert payload[0]["road_names"] == ["М-10"]
    stress.summary.assert_any_call("stress", "Московская область")
    roads.submit_closure.assert_not_called()
