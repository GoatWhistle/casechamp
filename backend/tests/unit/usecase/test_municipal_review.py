from unittest.mock import Mock

from app.usecase.chat_calculation_review import CalculationReview, CalculationReviews
from app.usecase.municipal_brief import municipal_brief
from app.usecase.municipal_scenarios import MunicipalTrafficEffects, MunicipalTrafficMetrics
from app.usecase.municipal_social import MunicipalSocialEffect, MunicipalSocialPoint
from app.usecase.traffic import (
    TrafficAlternative,
    TrafficAssignmentProgress,
    TrafficIndexChange,
    TrafficJob,
    TrafficMetrics,
    TrafficScope,
)


def test_municipal_review_keeps_negative_effects_and_uses_local_metrics() -> None:
    municipal, historical = Mock(), Mock()
    metric = TrafficMetrics(20, 3, 4, 0.0001, True)
    municipal.get.return_value = TrafficJob(
        'municipal-test', TrafficScope(), status='completed',
        alternatives=[TrafficAlternative('closure', 'closure', [1], 1., -10., metric, [],
            indices=[TrafficIndexChange('district', 100., 95., -5., -5., 1000)])],
    )
    municipal.effects.return_value = MunicipalTrafficEffects('district',
        MunicipalTrafficMetrics(5., 1, 0.), MunicipalTrafficMetrics(8., 2, 3.))
    review = CalculationReviews(None, None, traffic=historical, municipal=municipal)
    prompt = review.prompt(CalculationReview(traffic_ids=('municipal-test',)))
    assert '"delta": -5.0' in prompt
    assert '"vehicle_hours_on_local_edges": 8.0' in prompt
    assert '"social_access_recalculated": false' in prompt
    historical.get.assert_not_called()


def test_agent_review_reads_social_effects_once_and_preserves_sample_coverage() -> None:

    municipal = Mock()
    points = tuple(MunicipalSocialPoint(
        str(index), f'Village {index}', 45., 42., 20., None, None,
        'hospital', None, None, False, True,
    ) for index in range(12))
    municipal.effects.return_value = MunicipalTrafficEffects(
        'district', MunicipalTrafficMetrics(5., 1, 0.), MunicipalTrafficMetrics(8., 2, 3.),
        social=(MunicipalSocialEffect('N01', 60., status='available', reason=None,
                                      reference_points=12, lost_routes=12, points=points),
                MunicipalSocialEffect('N05', 20.)),
    )
    result = municipal_brief(TrafficJob('municipal-test', TrafficScope(), status='completed'), municipal)
    municipal.effects.assert_called_once_with('municipal-test')
    assert result['social_access_recalculated'] is True
    assert result['social_recalculated_criteria'] == ['N01']
    effects = result['municipal_effects']
    assert isinstance(effects, dict)
    social = effects['social'][0]
    assert social['lost_routes'] == 12
    assert social['affected_points_total'] == 12
    assert social['points_truncated'] is True
    assert len(social['points']) == 10
    assert len(municipal.effects.return_value.social[0].points) == 12


def test_running_scenario_does_not_claim_social_results() -> None:

    municipal = Mock()
    result = municipal_brief(TrafficJob('municipal-test', TrafficScope(), status='running',
                                      assignment_progress=TrafficAssignmentProgress(3, .002)), municipal)
    assert result['assignment_progress'] == {'iteration': 3, 'relative_gap': .002, 'tolerance': .001}
    municipal.effects.assert_not_called()
    assert result['social_access_recalculated'] is False
    assert result['social_recalculated_criteria'] == []
    assert 'municipal_effects' not in result
