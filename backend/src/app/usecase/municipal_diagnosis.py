from dataclasses import asdict

from app.usecase.municipal_overview import MunicipalOverview


def municipal_diagnosis(overview: MunicipalOverview) -> dict[str, object]:
    measured = [item for item in overview.items if item.connectivity.value is not None]
    candidates = [item for item in measured
                  if item.difference_from_region is not None and item.difference_from_region < 0]
    selected = candidates[0] if candidates else None
    regional = overview.region_connectivity.value
    return {
        'region_id': overview.region_id,
        'status': 'candidate_found' if selected else 'no_confirmed_candidate',
        'selection_basis': 'lowest_saved_city_connectivity_below_region',
        'compared_municipalities': len(measured),
        'unmeasured_municipalities': len(overview.items) - len(measured),
        'candidate': asdict(selected) if selected else None,
        'region_connectivity': asdict(overview.region_connectivity),
        'below_region_percent': (
            -100 * selected.difference_from_region / regional
            if selected and selected.difference_from_region is not None and regional
            else None
        ),
        'tied_lowest_municipalities': [item.municipality_id for item in candidates
                                     if selected and item.connectivity.value == selected.connectivity.value],
        'traffic_status': 'not_checked',
        'service_status': 'not_checked',
        'causal_explanation_verified': False,
        'model_version': overview.model_version,
        'artifact_version': overview.artifact_version,
        'source_table': overview.source_table,
        'season': overview.season,
    }
