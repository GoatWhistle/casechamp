from dataclasses import asdict

from app.usecase.municipal_comparison import municipal_comparison
from app.usecase.municipal_scenarios import MunicipalScenarios
from app.usecase.traffic import TrafficJob


def municipal_brief(job: TrafficJob, scenarios: MunicipalScenarios) -> dict[str, object]:
    value = asdict(job)
    for key in ('roads', 'zones', 'provenance'):
        value.pop(key)
    for alternative in value['alternatives']:
        alternative.pop('roads')
    effects = scenarios.effects(job.id) if job.status == 'completed' else None
    if effects is not None:
        value['municipal_effects'] = asdict(effects)
    value['comparison'] = municipal_comparison(job, effects)
    value['not_recalculated'] = ['walking_access', 'public_transport_access']
    value['load_basis'] = 'synthetic_fixed_od'
    value['network_totals_scope'] = 'stored_baseline_network'
    criteria = [item.criterion_id for item in effects.social if item.status == 'available'] if effects else []
    value['social_access_recalculated'] = bool(criteria)
    value['social_recalculated_criteria'] = criteria
    if effects:
        for item in value['municipal_effects']['social']:
            affected = [point for point in item['points'] if point['crossed_threshold']
                        or point['route_after_exists'] is False
                        or (point['added_minutes'] is not None and abs(point['added_minutes']) > 1e-6)]
            item['affected_points_total'] = len(affected)
            item['points_truncated'] = len(affected) > 10
            item['points'] = affected[:10]
    return value
