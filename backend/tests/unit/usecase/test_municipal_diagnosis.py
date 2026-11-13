import json
from unittest.mock import Mock, patch

from app.adapter.chat.municipal_tools import MunicipalTools
from app.domain.municipal_metrics import MunicipalMetric
from app.usecase.municipal_diagnosis import municipal_diagnosis
from app.usecase.municipal_overview import MunicipalOverview, MunicipalOverviewItem


def metric(value: float | None) -> MunicipalMetric:
    return MunicipalMetric('hansen_idx', value, 'available' if value is not None else 'unavailable',
                           None, 'index_points', 100, 80, 10, 8, .8)


def overview(values: list[float | None], regional: float = 100.) -> MunicipalOverview:
    return MunicipalOverview('region', [MunicipalOverviewItem(
        str(index), f'District {index}', metric(value),
        value - regional if value is not None else None, [],
    ) for index, value in enumerate(values)], metric(regional), 'model', 'artifact', 'saved')


def test_diagnosis_explains_comparison_without_inventing_road_causes() -> None:
    result = municipal_diagnosis(overview([20., 20., 80., None]))
    assert result['status'] == 'candidate_found'
    assert result['below_region_percent'] == 80.
    assert result['compared_municipalities'] == 3
    assert result['unmeasured_municipalities'] == 1
    assert result['tied_lowest_municipalities'] == ['0', '1']
    candidate = result['candidate']
    assert isinstance(candidate, dict)
    assert candidate['connectivity']['population_coverage'] == .8
    assert result['traffic_status'] == 'not_checked'
    assert result['service_status'] == 'not_checked'
    assert result['causal_explanation_verified'] is False
    assert result['artifact_version'] == 'artifact'


def test_missing_or_equal_indices_do_not_create_a_problem_district() -> None:
    for source in [overview([None]), overview([100., 100.]), overview([0.], 0.)]:
        result = municipal_diagnosis(source)
        assert result['status'] == 'no_confirmed_candidate'
        assert result['candidate'] is None
        assert result['below_region_percent'] is None


def test_agent_diagnosis_uses_connectivity_ranking_without_starting_a_scenario() -> None:
    indices, scenarios = Mock(), Mock()
    indices.services = None
    with patch('app.adapter.chat.municipal_tools.municipal_overview',
               return_value=overview([20., 80.])) as load:
        result = json.loads(MunicipalTools(indices, scenarios).municipal_analysis(
            Mock(), 'diagnose', region_id='region', criterion_id='N01',
        ))
    assert load.call_args.args[3] is None
    assert result['candidate']['municipality_id'] == '0'
    assert result['below_region_percent'] == 80.
    scenarios.submit.assert_not_called()
    indices.run.assert_not_called()
