from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import AccessRow
from app.usecase.municipal_access import MunicipalAccessPoint, MunicipalAccessResult
from app.usecase.municipal_road_candidates import MunicipalRoadCandidates
from app.usecase.municipal_scenarios import MunicipalTrafficBaseline, MunicipalTrafficCorridor
from app.usecase.municipalities import MunicipalCollection, Municipality
from app.usecase.road_records import RoadSegment, RoadView
from app.usecase.traffic import TrafficJob, TrafficRoad, TrafficScope


def finder() -> tuple[MunicipalRoadCandidates, Mock, Mock]:
    municipality = Municipality('district', 'region', 'District', 6,
        [[[(40., 44.), (41., 44.), (41., 45.), (40., 45.), (40., 44.)]]],
        'source', 'today', 'sha', 'polygon', 1.)
    queries, graph, scenarios, access = Mock(), Mock(), Mock(), Mock()
    queries.run.return_value = MunicipalCollection('region', [municipality], None)
    graph.view.return_value = RoadView([
        RoadSegment(1, 'Main', 'primary', 60., [[40.1, 44.1], [40.2, 44.1]]),
        RoadSegment(2, 'Local', 'residential', 30., [[40.1, 44.2], [40.2, 44.2]]),
        RoadSegment(4, 'Main', 'primary', 60., [[40.3, 44.1], [40.4, 44.1]]),
        RoadSegment(3, 'Outside', 'motorway', 90., [[42., 44.1], [42.1, 44.1]]),
    ], 3, False, 'graph-v1')
    scenarios.baseline.side_effect = DataUnavailable('Not published')
    access.run.return_value = MunicipalAccessResult(
        'region', 'district', 'N01', 'sha', 'run', 'today', 'minutes', 'car', 60.,
        1, 1, 0, 0, 1, 90., 90., [MunicipalAccessPoint(
            AccessRow('village', 'Village', 100, 44.1, 40.15, 'hospital', 90., 30., 'exceeded'),
            None, True,
        )], 1, 0, 100,
    )
    return MunicipalRoadCandidates(queries, graph, scenarios, access), scenarios, access


def test_search_works_before_load_and_does_not_invent_route_dependencies() -> None:
    search, scenarios, _ = finder()
    result = search.run('region', 'district')
    rows = result['candidates']
    assert isinstance(rows, list)
    assert [row['way_id'] for row in rows] == [1, 2]
    assert rows[0]['bottleneck_confirmed'] is False
    assert rows[0]['nearby_access_samples'][0]['name'] == 'Village'
    assert rows[0]['nearby_access_samples'][0]['route_uses_segment'] is None
    assert rows[0]['directed_segments'] == []
    assert result['traffic_status'] == 'unavailable'
    assert result['detour_status'] == 'not_checked'
    assert result['ranking_basis'] == 'road_class_then_reference_proximity'
    assert result['one_sample_segment_per_road_name'] is True
    scenarios.submit.assert_not_called()


def test_saved_load_ranks_candidates_without_excluding_non_widenable_roads() -> None:
    search, scenarios, _ = finder()
    scenarios.baseline.side_effect = None
    scenarios.baseline.return_value = MunicipalTrafficBaseline(
        'published', 'district', [MunicipalTrafficCorridor(2, 1.5, 10., 1.,
        capacity_eligible=False, capacity_reason='shared_lane')],
        [TrafficRoad(2, [[40.2, 44.2], [40.1, 44.2]], 10., 10., 1.5, 1.5,
                     edge_index=9, reverse_edge_index=4)], .001, None, 'artifact',
        TrafficJob('baseline', TrafficScope()),
    )
    result = search.run('region', 'district', limit=1)
    rows = result['candidates']
    assert isinstance(rows, list)
    assert rows[0]['way_id'] == 2
    assert rows[0]['directed_segments'][0]['edge_index'] == 9
    assert rows[0]['corridor_load']['capacity_eligible'] is False
    assert result['traffic_artifact_sha256'] == 'artifact'


def test_missing_access_preserves_roads_and_invalid_scope_is_rejected() -> None:
    search, _, access = finder()
    access.run.side_effect = DataUnavailable('No measurements')
    result = search.run('region', 'district')
    assert result['access_status'] == 'unavailable'
    assert result['status'] == 'candidates_found'
    with pytest.raises(InvalidQuery):
        search.run('region', 'outside')
    with pytest.raises(InvalidQuery):
        search.run('region', 'district', limit=0)
