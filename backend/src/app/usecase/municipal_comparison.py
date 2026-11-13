from app.usecase.municipal_scenarios import MunicipalTrafficEffects
from app.usecase.traffic import TrafficJob


def municipal_comparison(job: TrafficJob, effects: MunicipalTrafficEffects | None) -> list[dict[str, object]]:
    if job.status != 'completed' or not job.alternatives:
        return []
    alternative = job.alternatives[0]
    rows = [comparison('city_connectivity', item.region, item.before, item.after, 'index_points')
            for item in alternative.indices]
    if job.baseline:
        for key, unit in [('vehicle_hours', 'vehicle_hours'), ('unserved_vehicles', 'vehicles'),
                          ('overloaded_edges', 'directed_edges'), ('mean_trip_minutes', 'minutes')]:
            rows.append(comparison(key, 'baseline_network', getattr(job.baseline, key),
                                   getattr(alternative.after, key), unit))
    if effects:
        for key, unit in [('vehicle_hours_on_local_edges', 'vehicle_hours'),
                          ('overloaded_directed_edges', 'directed_edges'), ('unserved_departures', 'vehicles')]:
            rows.append(comparison(key, effects.municipality_id, getattr(effects.before, key),
                                   getattr(effects.after, key), unit))
        for social in effects.social:
            available = social.status == 'available' and social.reference_points > 0
            before = 100 * social.before_within / social.reference_points if available else None
            after = 100 * social.after_within / social.reference_points if available else None
            row = comparison(social.criterion_id, effects.municipality_id, before, after, 'reference_point_percent')
            row.update({'threshold_minutes': social.threshold_minutes, 'reference_points': social.reference_points,
                        'unresolved_points': social.unresolved_points, 'reason': social.reason,
                        'source_sha256': social.source_sha256})
            rows.append(row)
    return rows


def comparison(metric: str, scope: str, before: float | None, after: float | None, unit: str) -> dict[str, object]:
    return {'metric': metric, 'scope': scope, 'unit': unit, 'before': before, 'after': after,
            'delta': after - before if before is not None and after is not None else None,
            'status': 'available' if before is not None and after is not None else 'unavailable'}
