from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock

from tests.unit.usecase.test_index_map import row

from app.domain.normative.index import reference_index_values
from app.domain.normative.model import AccessRow
from app.domain.normative.scenario_index import ScenarioIndex, scenario_policy
from app.usecase.normative.index_map import IndexMapQueries, IndexMapRepository, value_range
from app.usecase.normative.indices import IndexBasisRepository, RegionalIndices
from app.usecase.normative.regional_measurements import RegionalMeasurementRepository
from app.usecase.normative.scenario_indices import ScenarioIndexRepository


def model() -> ScenarioIndex:
    point = AccessRow("p", "Point", 100, 55, 65, "target", 45, None, "unknown")
    policy = scenario_policy("N06")
    values = reference_index_values([point], policy.unit, policy.thresholds)
    return ScenarioIndex("R", "N06", "run", "2026-11-12", policy, values, values)


def test_scenario_value_keeps_missing_legal_basis_and_does_not_read_full_measurement() -> None:
    bases = Mock(spec=IndexBasisRepository)
    bases.region_exists.return_value = True
    bases.basis.return_value = None
    measurements = Mock(spec=RegionalMeasurementRepository)
    models = Mock(spec=ScenarioIndexRepository)
    models.latest.return_value = model()
    result = RegionalIndices(
        cast(IndexBasisRepository, bases),
        cast(RegionalMeasurementRepository, measurements),
        models=cast(ScenarioIndexRepository, models),
    ).latest("R", "N06")
    assert result.status == "basis_missing" and result.basis is None
    assert result.scenario == [] and not result.legal_compliance_confirmed
    assert result.model_index is not None
    assert result.model_index.scenario[0].population_share_percent == 100
    measurements.get.assert_not_called()


def test_map_uses_scenario_only_where_normative_value_is_unavailable() -> None:
    source = row()
    repository = Mock(spec=IndexMapRepository)
    repository.inputs.return_value = [source, replace(source, region_id="Missing", basis=None)]
    models = Mock(spec=ScenarioIndexRepository)
    models.regions.return_value = [model(), replace(model(), region_id="Missing")]
    result = IndexMapQueries(
        cast(IndexMapRepository, repository),
        lambda: datetime.now(UTC),
        cast(ScenarioIndexRepository, models),
    ).regions("N06")
    assert result[0].status == "ready" and result[0].value_min == 70
    assert result[1].status == "scenario_ready" and result[1].value_min == 100
    assert not result[1].legal_compliance_confirmed


def test_scenario_keeps_unknown_routes_in_denominator_without_inventing_population() -> None:
    known = AccessRow("a", "A", 100, 55, 65, "target", 30, None, "unknown")
    missing = replace(known, id="b", minutes=None, population=None)
    result = reference_index_values([known, missing], "minutes", (60,))[0]
    assert result.point_share_percent == 50 and result.unresolved_points == 1
    assert result.population is None and result.population_share_percent is None


def test_fire_response_share_counts_residents_not_settlement_points() -> None:
    city = AccessRow("city", "City", 900, 55, 65, "depot", 5, None, "unknown")
    village = AccessRow("village", "Village", 100, 55, 65, "depot", 15, None, "unknown")
    policy = scenario_policy("N03")
    values = reference_index_values([city, village], policy.unit, policy.thresholds)
    index = ScenarioIndex("R", "N03", "run", "2026-11-12", policy, values, values)
    assert policy.weighting == "population"
    assert value_range(index.scenario, policy.weighting) == (90, 100)
    assert values[0].point_share_percent == 50
