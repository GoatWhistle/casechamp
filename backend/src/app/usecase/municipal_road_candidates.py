from dataclasses import asdict, dataclass
from math import cos, hypot, radians

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.municipal_metrics import municipal_contains
from app.usecase.municipal_access import MunicipalAccessQueries, MunicipalAccessResult
from app.usecase.municipal_scenarios import (
    MunicipalScenarios,
    MunicipalTrafficBaseline,
    MunicipalTrafficCorridor,
)
from app.usecase.municipalities import MunicipalityQueries
from app.usecase.road_graph import RoadGraph

ROAD_PRIORITY = {'motorway': 0, 'trunk': 1, 'primary': 2, 'secondary': 3, 'tertiary': 4}


@dataclass(frozen=True)
class RoadCandidate:
    way_id: int
    name: str
    highway: str
    coordinates: list[list[float]]
    corridor_load: MunicipalTrafficCorridor | None
    bottleneck_confirmed: bool = False


class MunicipalRoadCandidates:
    def __init__(self, municipalities: MunicipalityQueries, graph: RoadGraph,
                 scenarios: MunicipalScenarios | None, access: MunicipalAccessQueries | None) -> None:
        self.municipalities = municipalities
        self.graph = graph
        self.scenarios = scenarios
        self.access = access

    def run(self, region: str, identifier: str, criterion: str = 'N01', limit: int = 5) -> dict[str, object]:
        if not 1 <= limit <= 10:
            raise InvalidQuery('Return between 1 and 10 road candidates')
        municipality = next((item for item in self.municipalities.run(region).items
                             if item.id == identifier), None)
        if municipality is None:
            raise InvalidQuery('Municipality is not available in this region')
        vertices = [point for polygon in municipality.coordinates for ring in polygon for point in ring]
        if not vertices:
            raise DataUnavailable('Municipal boundary is unavailable')
        bounds = (min(x for x, _ in vertices), min(y for _, y in vertices),
                  max(x for x, _ in vertices), max(y for _, y in vertices))
        view = self.graph.view(*bounds, 10.)
        baseline, load_error = self._baseline(region, identifier)
        access, access_error = self._access(region, identifier, criterion)
        loads = {row.way_id: row for row in baseline.corridors} if baseline else {}
        rows = []
        for road in view.segments:
            for start, end in zip(road.coordinates, road.coordinates[1:]):
                midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
                if not municipal_contains(*midpoint, municipality.coordinates):
                    continue
                load = loads.get(road.way_id)
                rows.append(RoadCandidate(road.way_id, road.name, road.highway, [start, end], load))
        rows.sort(key=lambda row: (
            row.corridor_load is None,
            -row.corridor_load.peak_ratio if row.corridor_load else 0.,
            ROAD_PRIORITY.get(row.highway, 5), nearest_sample_distance(row.coordinates, access),
            row.name, row.way_id,
        ))
        selected: list[dict[str, object]] = []
        seen: set[str] = set()
        for row in rows:
            identity = row.name.strip().casefold() or str(row.way_id)
            if identity in seen:
                continue
            seen.add(identity)
            record = asdict(row)
            record['nearby_access_samples'] = nearby_samples(row.coordinates, access)
            record['directed_segments'] = [asdict(road) for road in baseline.roads
                                          if road.way_id == row.way_id and same_segment(road.coordinates, row.coordinates)] if baseline else []
            selected.append(record)
            if len(selected) == limit:
                break
        return {
            'region_id': region, 'municipality_id': identifier, 'municipality_name': municipality.name,
            'status': 'candidates_found' if selected else 'no_candidates_in_graph_view',
            'ranking_basis': 'corridor_peak_load_then_road_class_and_reference_proximity' if baseline else 'road_class_then_reference_proximity',
            'candidates': selected, 'matched_local_segments': len(rows),
            'candidate_limit': limit, 'one_sample_segment_per_road_name': True,
            'graph_version': view.version, 'graph_detail': view.detail, 'graph_truncated': view.truncated,
            'membership_method': 'edge_midpoint_in_municipal_polygon',
            'traffic_status': 'available' if baseline else 'unavailable', 'traffic_reason': load_error,
            'baseline_id': baseline.baseline_id if baseline else None,
            'load_preliminary': baseline.view.stage == 'preliminary' if baseline else None,
            'demand_zones': baseline.demand_zones if baseline else None,
            'demand_cell_km': baseline.demand_cell_km if baseline else None,
            'traffic_artifact_sha256': baseline.artifact_sha256 if baseline else None,
            'access_status': 'available' if access else 'unavailable', 'access_reason': access_error,
            'access_source_sha256': access.source_sha256 if access else None,
            'access_measured_at': access.measured_at if access else None,
            'access_sample_size': len(access.points) if access else 0,
            'access_total_reference_points': access.total if access else None,
            'access_deficit_points': access.deficit_points if access else None,
            'access_sample_basis': 'most_remote_saved_reference_points',
            'geographic_sample_radius_km': 5.,
            'association_basis': 'geographic_proximity_only_not_route_dependency',
            'detour_status': 'not_checked', 'scenario_effect_status': 'not_checked',
        }

    def _baseline(self, region: str, identifier: str) -> tuple[MunicipalTrafficBaseline | None, str | None]:
        if self.scenarios is None:
            return None, 'traffic_not_configured'
        try:
            return self.scenarios.baseline(region, identifier), None
        except DataUnavailable as error:
            return None, error.message

    def _access(self, region: str, identifier: str, criterion: str) -> tuple[MunicipalAccessResult | None, str | None]:
        if self.access is None:
            return None, 'access_not_configured'
        try:
            return self.access.run(region, identifier, criterion, deficit_only=False, limit=100), None
        except DataUnavailable as error:
            return None, error.message


def same_segment(first: list[list[float]], second: list[list[float]]) -> bool:
    return first == second or first == list(reversed(second))


def nearby_samples(line: list[list[float]], access: MunicipalAccessResult | None) -> list[dict[str, object]]:
    if access is None:
        return []
    samples = []
    for point in access.points:
        row = point.row
        if row.longitude is None or row.latitude is None:
            continue
        distance = segment_distance_km(row.longitude, row.latitude, line)
        if distance > 5.:
            continue
        samples.append({
            'origin_id': row.id, 'name': row.name, 'distance_to_segment_km': distance,
            'travel_minutes': row.minutes, 'state': row.state,
            'facility_id': row.facility_id,
            'facility_name': point.facility.name if point.facility else None,
            'route_uses_segment': None,
        })
    samples.sort(key=lambda row: float(str(row['distance_to_segment_km'])))
    return samples[:3]


def nearest_sample_distance(line: list[list[float]], access: MunicipalAccessResult | None) -> float:
    if access is None:
        return float('inf')
    return min((segment_distance_km(point.row.longitude, point.row.latitude, line)
                for point in access.points if point.row.longitude is not None
                and point.row.latitude is not None), default=float('inf'))


def segment_distance_km(lon: float, lat: float, line: list[list[float]]) -> float:
    scale_x = 111.195 * cos(radians(lat))
    a, b = line
    ax, ay = (a[0] - lon) * scale_x, (a[1] - lat) * 111.195
    bx, by = (b[0] - lon) * scale_x, (b[1] - lat) * 111.195
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = max(0., min(1., -(ax * dx + ay * dy) / length)) if length else 0.
    return hypot(ax + t * dx, ay + t * dy)
