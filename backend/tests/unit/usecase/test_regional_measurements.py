from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.comparison import compare_routes
from app.domain.normative.model import AccessRow, Origin
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.regional_catalog import RegionalCatalogQueries, RegionalCatalogRepository
from app.usecase.normative.regional_measurements import (
    RegionalMeasurementRepository,
    RegionalMeasurements,
)


def queries() -> tuple[RegionalMeasurements, Mock, Mock]:
    catalog = Mock(spec=RegionalCatalogRepository)
    catalog.region_name.return_value = "Selected region"
    catalog.candidates.return_value = [replace(facility(), service="medical")]
    repository = Mock(spec=RegionalMeasurementRepository)
    repository.origins.return_value = [Origin("p", "Place", 100, 2, 0.1, 55, 65)]
    routing = Mock(spec=NormativeRouting)
    routing.revision = "graph-one"
    routing.missing_ways.return_value = []
    routing.evaluate.return_value = [
        AccessRow(
            "p", "Place", 100, 55, 65, "f", 7, 0, "within", routing_node=2, approach_metres=100
        )
    ]
    usecase = RegionalMeasurements(
        RegionalCatalogQueries(cast(RegionalCatalogRepository, catalog)),
        cast(RegionalMeasurementRepository, repository),
        cast(NormativeRouting, routing),
        lambda: datetime(2026, 11, 12, tzinfo=UTC),
    )
    return usecase, repository, routing


def test_regional_medical_measurements_keep_physical_cost_without_cardiology_claim() -> None:
    usecase, repository, _ = queries()
    result = usecase.calculate("R", "N01", [])
    repository.origins.assert_called_once_with("R")
    repository.save.assert_called_once_with(result)
    assert result.region_id == "R"
    assert result.rows[0].minutes == 7
    assert result.rows[0].state == "unknown"
    assert result.rows[0].population is None
    assert result.rows[0].threshold_minutes is None
    assert result.rows[0].excess_minutes is None
    assert result.qualification == "physical_only"
    assert result.model_revision == "regional-road-v1"


@pytest.mark.parametrize("criterion", ["N03", "N04", "N09"])
def test_dedicated_models_cannot_silently_become_car_measurements(criterion: str) -> None:
    usecase, repository, routing = queries()
    with pytest.raises((InvalidQuery, DataUnavailable)):
        usecase.calculate("R", criterion, [])
    repository.save.assert_not_called()
    routing.evaluate.assert_not_called()


def test_empty_regional_origins_do_not_fall_back_to_the_pilot() -> None:
    usecase, repository, routing = queries()
    repository.origins.return_value = []
    with pytest.raises(DataUnavailable):
        usecase.calculate("R", "N05", [])
    repository.origins.assert_called_once_with("R")
    repository.save.assert_not_called()
    routing.evaluate.assert_not_called()


def test_missing_scenario_way_is_rejected_before_running_or_saving() -> None:
    usecase, repository, routing = queries()
    routing.missing_ways.return_value = [999]
    with pytest.raises(InvalidQuery):
        usecase.calculate("R", "N05", [999])
    repository.save.assert_not_called()
    routing.evaluate.assert_not_called()


def test_small_receipt_counts_the_scenario_paths_after_losses_and_restorations() -> None:
    usecase, _, _ = queries()
    result = usecase.calculate("R", "N05", [])
    first = result.rows[0]
    baseline = [
        replace(first, id="lost"),
        replace(first, id="restored", minutes=None),
        replace(first, id="paired"),
    ]
    scenario = [
        replace(baseline[0], minutes=None),
        replace(baseline[1], minutes=9),
        replace(baseline[2], minutes=10),
    ]
    changed = replace(
        result,
        baseline_rows=baseline,
        rows=scenario,
        comparison=compare_routes(baseline, scenario, "minutes"),
    )
    receipt = changed.receipt()
    assert receipt.origins == 3
    assert receipt.measured_paths == 2
    assert receipt.run_id == changed.run_id
    assert not hasattr(receipt, "rows")
