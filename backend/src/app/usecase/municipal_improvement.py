from dataclasses import asdict

from app.domain.errors import DataUnavailable
from app.usecase.municipal_scenarios import MunicipalScenarioRequest, MunicipalScenarios
from app.usecase.traffic import TrafficJob


def propose_lane(scenarios: MunicipalScenarios, region: str, municipality: str) -> tuple[dict[str, object], TrafficJob | None]:
    try:
        baseline = scenarios.baseline(region, municipality)
    except DataUnavailable as error:
        return {'status': 'awaiting_baseline', 'reason': error.message,
                'effect_status': 'not_calculated'}, None
    corridors = {row.way_id: row for row in baseline.corridors if row.capacity_eligible}
    candidates = [road for road in baseline.roads if road.way_id in corridors
                  and road.edge_index is not None and road.shared_lane is False
                  and road.flow_before > 0 and road.ratio_before is not None]
    candidates.sort(key=lambda road: (-(road.ratio_before or 0), -road.flow_before,
                                     road.way_id, road.edge_index or 0))
    if not candidates:
        return {'status': 'awaiting_routing_baseline' if baseline.view.stage == 'preliminary' else 'no_supported_candidate', 'baseline_id': baseline.baseline_id,
                'selection_scope': 'published_load_overlay', 'effect_status': 'not_calculated'}, None
    road = candidates[0]
    assert road.edge_index is not None
    preliminary = baseline.view.stage == 'preliminary'
    job = None if preliminary else scenarios.submit(MunicipalScenarioRequest(
        baseline.baseline_id, region, municipality, 'capacity', [road.way_id], [road.edge_index],
    ))
    return {
        'status': 'awaiting_routing_baseline' if preliminary else 'evaluation_started',
        'calculation_id': job.id if job else None,
        'relative_gap': baseline.relative_gap,
        'capacity_deficit_confirmed': (road.ratio_before or 0) > 1 and not preliminary,
        'baseline_id': baseline.baseline_id, 'baseline_sha256': baseline.artifact_sha256,
        'proposal': {'change': 'capacity', 'extra_lanes': 1, 'way_id': road.way_id,
                     'road_name': corridors[road.way_id].name, 'edge_index': road.edge_index,
                     'direction': 'first_coordinate_to_last_coordinate',
                     'coordinates': road.coordinates, 'opposite_direction_unchanged': True},
        'selection_basis': 'highest_directed_load_ratio_then_flow_among_supported_visible_edges',
        'selection_scope': 'published_load_overlay_not_global_optimum',
        'before': asdict(road), 'effect_status': 'not_calculated' if preliminary else 'pending',
        'construction_feasibility': 'not_verified',
    }, job
