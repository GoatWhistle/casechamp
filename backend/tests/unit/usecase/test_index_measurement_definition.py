from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.domain.normative.test_index import basis
from tests.unit.usecase.test_index_map import row
from tests.unit.usecase.test_regional_index_modes import evaluate
from tests.unit.usecase.test_regional_measurements import queries

from app.domain.errors import DataUnavailable
from app.domain.normative.comparison import compare_routes
from app.domain.normative.index import IndexBasis, index_values
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow
from app.usecase.normative.index_map import IndexMapQueries, IndexMapRepository
from app.usecase.normative.indices import (
    IndexBasisRepository,
    RegionalIndexCache,
    RegionalIndices,
)
from app.usecase.normative.regional_measurements import (
    RegionalMeasurement,
    RegionalMeasurementRepository,
)
from app.usecase.normative.regional_receipt import RegionalMeasurementHead
from app.usecase.normative.regional_route import trace_regional_route
from app.usecase.normative.regional_view import RegionalPointDetail

PARCEL = MeasurementDefinition.STOP_PAVILION_PARCEL_BOUNDARY


def parcel_basis() -> IndexBasis:
    return replace(
        basis(),
        criterion_id="N09",
        unit="metres",
        required_mode="walk",
        thresholds=(500, 800),
        required_measurement_definition=PARCEL,
    )


def test_distance_inside_threshold_is_not_coverage_when_the_measured_entities_differ() -> None:
    point = AccessRow(
        "home", "Home", None, 55, 65, "stop", None, None, "unknown", distance_metres=300
    )
    with pytest.raises(ValueError, match="measurement definition"):
        index_values([point], parcel_basis())
    assert index_values([point], parcel_basis(), PARCEL)[0].point_share_percent == 100


def test_incompatible_metadata_blocks_full_rows_and_an_incompatible_cache() -> None:
    bases = Mock(spec=IndexBasisRepository)
    bases.region_exists.return_value = True
    bases.basis.return_value = parcel_basis()
    measurements = Mock(spec=RegionalMeasurementRepository)
    measurements.latest_head.return_value = RegionalMeasurementHead(
        "run", "2026-11-12", MeasurementDefinition.SINGLE_REFERENCE_POINT
    )
    cache = Mock(spec=RegionalIndexCache)
    cache.latest.return_value = replace(evaluate("walk"), basis=parcel_basis())
    result = RegionalIndices(
        cast(IndexBasisRepository, bases),
        cast(RegionalMeasurementRepository, measurements),
        cast(RegionalIndexCache, cache),
    ).latest("R", "N09")
    assert result.status == "measurement_incompatible"
    assert result.run_id == "run" and result.scenario == []
    measurements.get.assert_not_called()
    measurements.latest.assert_not_called()
    measurements.latest_receipt.assert_not_called()


def test_country_map_cannot_use_a_stale_numeric_summary_for_different_entities() -> None:
    source = row()
    source = replace(source, basis=parcel_basis())
    repository = Mock(spec=IndexMapRepository)
    repository.inputs.return_value = [source]
    value = IndexMapQueries(
        cast(IndexMapRepository, repository), lambda: datetime.now(UTC)
    ).regions("N09")[0]
    assert value.status == "measurement_incompatible"
    assert value.value_min is None and value.value_max is None


def test_publisher_rejects_numeric_values_with_incompatible_measurement_metadata() -> None:
    index = replace(evaluate("walk"), basis=parcel_basis())
    repository = Mock(spec=IndexMapRepository)
    assert not IndexMapQueries(
        cast(IndexMapRepository, repository), lambda: datetime.now(UTC)
    ).publish(index)
    repository.save.assert_not_called()


def test_existing_route_model_cannot_replay_a_relabelled_measurement() -> None:
    usecase, _, routing = queries()
    result = usecase.calculate("R", "N01", [])
    view = replace(result.view(), measurement_definition=PARCEL)
    point = RegionalPointDetail(result.rows[0], result.facilities[0])
    with pytest.raises(DataUnavailable):
        trace_regional_route(view, point, "scenario", routing, None, None)
    routing.trace.assert_not_called()


@pytest.mark.parametrize("change", [None, "definition", "run"])
def test_matching_definitions_work_and_a_changed_snapshot_is_checked_again(
    change: str | None,
) -> None:
    point = AccessRow(
        "home", "Home", None, 55, 65, "stop", None, None, "unknown", distance_metres=300
    )
    measurement = RegionalMeasurement(
        "run",
        "R",
        "Region",
        "N09",
        "stop",
        "graph",
        "2026-11-12",
        [],
        [point],
        [point],
        [],
        compare_routes([point], [point], "metres"),
        mode="walk",
        unit="metres",
        model_revision="test-parcel-model",
        measurement_definition=PARCEL,
    )
    bases = Mock(spec=IndexBasisRepository)
    bases.region_exists.return_value = True
    bases.basis.return_value = parcel_basis()
    measurements = Mock(spec=RegionalMeasurementRepository)
    measurements.latest_head.return_value = RegionalMeasurementHead(
        measurement.run_id, measurement.saved_at, measurement.measurement_definition
    )
    measurements.get.return_value = (
        replace(
            measurement,
            measurement_definition=MeasurementDefinition.SINGLE_REFERENCE_POINT,
        )
        if change == "definition"
        else measurement
    )
    if change == "run":
        measurements.get.return_value = replace(measurement, run_id="other")
    usecase = RegionalIndices(
        cast(IndexBasisRepository, bases),
        cast(RegionalMeasurementRepository, measurements),
    )
    if change == "run":
        with pytest.raises(DataUnavailable):
            usecase.latest("R", "N09")
        return
    result = usecase.latest("R", "N09")
    if change == "definition":
        assert result.status == "measurement_incompatible" and result.scenario == []
        assert result.run_id == "run"
    else:
        assert result.status == "ready" and result.measurement_definition == PARCEL
        assert result.scenario[0].point_share_percent == 100
