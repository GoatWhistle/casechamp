from dataclasses import replace
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable
from app.domain.normative.model import AccessRow, Criterion, Facility
from app.usecase.normative.interface import NormativeRepository, NormativeRouting
from app.usecase.normative.route import MODEL_REVISION, RouteContext, RouteGeometry, RouteStage
from app.usecase.normative.routes import NormativeRoutes


def context() -> RouteContext:
    return RouteContext(
        Criterion(
            "N05",
            "mfc",
            "178",
            "5",
            "source",
            "2023-02-08",
            60,
            "minutes",
            "car",
            "region",
            "placement",
            "unconfirmed",
        ),
        "network-1",
        MODEL_REVISION,
        AccessRow(
            "o", "Origin", 10, 55, 65, "f", 12, None, "within", routing_node=1, approach_metres=20
        ),
        Facility(
            "f",
            "mfc",
            "Office",
            "Address",
            "source",
            "2026-11-12",
            55.1,
            65.1,
            "coordinate-source",
            "geocoded_building",
        ),
        [123],
    )


def queries(saved: RouteContext, minutes: float = 12) -> tuple[NormativeRoutes, Mock]:
    repository = cast(NormativeRepository, SimpleNamespace(route_context=lambda *_: saved))
    trace = Mock(return_value=RouteGeometry([(65, 55), (65.1, 55.1)], [], minutes, None))
    road = cast(NormativeRouting, SimpleNamespace(trace=trace))
    return NormativeRoutes(repository, road, None), trace


def test_unversioned_history_cannot_be_traced_with_current_algorithm() -> None:
    usecase, trace = queries(replace(context(), model_revision="unversioned"))
    with pytest.raises(DataUnavailable, match="unversioned"):
        usecase.get("run", "o", "scenario")
    trace.assert_not_called()


def test_reconstructed_cost_must_equal_the_saved_cost() -> None:
    usecase, _ = queries(context(), minutes=13)
    with pytest.raises(DataUnavailable, match="does not match"):
        usecase.get("run", "o", "scenario")


@pytest.mark.parametrize("stage,closed", [("baseline", []), ("scenario", [123])])
def test_route_uses_saved_attachment_revision_and_selected_stage(
    stage: str, closed: list[int]
) -> None:
    usecase, trace = queries(context())
    result = usecase.get("run", "o", cast(RouteStage, stage))
    origin, _, actual_closed, revision = trace.call_args.args
    assert origin.node == 1
    assert origin.snap_km == 0.02
    assert actual_closed == closed
    assert revision == "network-1"
    assert result.model_revision == MODEL_REVISION


@pytest.mark.parametrize("version", ["normative-v3", "normative-v4", "normative-v5", "normative-v6"])
def test_old_route_costs_remain_replayable_without_reinterpreting_rule_conditions(
    version: str,
) -> None:
    usecase, _ = queries(replace(context(), model_revision=version))
    result = usecase.get("run", "o", "baseline")
    assert result.model_revision == version
    assert result.geometry.minutes == 12
