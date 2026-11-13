from app.usecase.municipal_comparison import municipal_comparison
from app.usecase.municipal_scenarios import MunicipalTrafficEffects, MunicipalTrafficMetrics
from app.usecase.municipal_social import MunicipalSocialEffect
from app.usecase.traffic import (
    TrafficAlternative,
    TrafficIndexChange,
    TrafficJob,
    TrafficMetrics,
    TrafficScope,
)


def test_comparison_preserves_zero_negative_and_unavailable_results() -> None:
    before = TrafficMetrics(100., 0., 5, .001, True)
    after = TrafficMetrics(110., 2., 4, .001, True)
    job = TrafficJob('job', TrafficScope(), status='completed', baseline=before,
        alternatives=[TrafficAlternative('a', 'capacity', [1], 1., None, after, [], indices=[
            TrafficIndexChange('district', 40., 40., 0., 0., 100),
            TrafficIndexChange('region', 80., 79., -1., -1.25, 1000)])])
    effects = MunicipalTrafficEffects('district', MunicipalTrafficMetrics(10., 1, 0.),
        MunicipalTrafficMetrics(9., 0, 2.), social=(
            MunicipalSocialEffect('N01', 60., status='available', reason=None,
                                 reference_points=10, before_within=5, after_within=6),
            MunicipalSocialEffect('N05', 20.),))
    rows = municipal_comparison(job, effects)
    assert rows[0]['delta'] == 0.
    assert rows[1]['delta'] == -1.
    assert next(row for row in rows if row['metric'] == 'vehicle_hours')['delta'] == 10.
    assert next(row for row in rows if row['metric'] == 'N01')['delta'] == 10.
    assert next(row for row in rows if row['metric'] == 'N05')['status'] == 'unavailable'
    assert municipal_comparison(TrafficJob('running', TrafficScope()), None) == []
