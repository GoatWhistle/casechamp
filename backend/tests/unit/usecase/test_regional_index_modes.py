from dataclasses import replace
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.domain.normative.test_index import basis

from app.domain.normative.comparison import compare_routes
from app.domain.normative.model import AccessRow
from app.usecase.normative.indices import IndexBasisRepository, RegionalIndex, RegionalIndices
from app.usecase.normative.regional_measurements import (
    RegionalMeasurement,
    RegionalMeasurementRepository,
)
from app.usecase.normative.regional_receipt import RegionalMeasurementHead


def evaluate(mode: str, regulation: str = "threshold") -> RegionalIndex:
    bases = Mock(spec=IndexBasisRepository)
    bases.region_exists.return_value = True
    bases.basis.return_value = replace(
        basis(),
        criterion_id="N04",
        required_mode=mode,
        regulation=regulation,
        unit="metres",
        thresholds=() if regulation == "not_regulated" else (500, 800),
    )
    row = AccessRow(
        "home", "Home", None, 55, 65, "school", None, None, "unknown", distance_metres=700
    )
    measurements = Mock(spec=RegionalMeasurementRepository)
    measurements.latest.return_value = RegionalMeasurement(
        "run",
        "R",
        "Region",
        "N04",
        "school",
        "graph",
        "2026-11-12",
        [],
        [row],
        [row],
        [],
        compare_routes([row], [row], "metres"),
        mode="walk",
        unit="metres",
    )
    saved = measurements.latest.return_value
    measurements.latest_head.return_value = RegionalMeasurementHead(
        saved.run_id, saved.saved_at, saved.measurement_definition
    )
    measurements.get.return_value = saved
    return RegionalIndices(
        cast(IndexBasisRepository, bases), cast(RegionalMeasurementRepository, measurements)
    ).latest("R", "N04")


@pytest.mark.parametrize("mode", ["car", "pedestrian_transit", "emergency_response"])
def test_incompatible_travel_mode_cannot_create_a_numeric_index(mode: str) -> None:
    result = evaluate(mode)
    assert result.status == "model_unavailable"
    assert result.scenario == []
    assert result.basis is not None


def test_explicitly_unregulated_accessibility_retains_source_without_an_invented_zero() -> None:
    result = evaluate("none", "not_regulated")
    assert result.status == "not_regulated"
    assert result.scenario == []
    assert result.basis is not None
    assert result.basis.thresholds == ()


def test_walking_index_uses_metres_and_keeps_contextual_variants_separate() -> None:
    result = evaluate("walk")
    assert result.status == "ready"
    assert [value.point_share_percent for value in result.scenario] == [0, 100]
    assert all(value.population_share_percent is None for value in result.scenario)
