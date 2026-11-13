import json
from dataclasses import asdict
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.usecase.test_transit_access import access, points

from app.adapter.chat.municipal_tools import MunicipalTools
from app.controller.transit import build_transit_router
from app.domain.transit_journey import TransitConnection
from app.usecase.transit_catalog import TransitSnapshot, TransitStop
from app.usecase.transit_queries import TransitPlace, TransitQueries


def queries() -> TransitQueries:
    origin, destination, stops = points()
    catalog = Mock()
    catalog.latest.return_value = TransitSnapshot('snapshot', '2026-11-05', 'source', 'sha', 'source_clock',
        False, False, False, [TransitStop(p.id, p.id, 'R', '26', p.latitude, p.longitude, 'pin', 'source', 'sha') for p in stops],
        [TransitConnection('bus', 'A', 'B', 600, 1200)])
    locations = Mock()
    locations.origin.return_value = TransitPlace(origin.id, 'Home', origin.latitude, origin.longitude, 'reference')
    locations.facility.return_value = TransitPlace(destination.id, 'Clinic', destination.latitude, destination.longitude, 'pin')
    return TransitQueries(catalog, locations, lambda region: access().walking)


def test_http_and_agent_share_journey_and_agent_omits_unused_walk_matrix() -> None:
    service = queries()
    app = FastAPI()
    app.include_router(build_transit_router(service))
    with TestClient(app) as client:
        response = client.post('/regions/R/transit-journeys', json={'origin_id': 'home', 'facility_id': 'clinic', 'departure_seconds': 0})
    assert response.status_code == 200
    context = Mock()
    context.deps.pending = []
    agent = json.loads(MunicipalTools(Mock(), None, transit=service).municipal_analysis(
        context, 'journey', 'R', origin_id='home', facility_id='clinic', departure_seconds=0,
    ))
    assert agent['result']['journey'] == response.json()['result']['journey']
    assert agent['result']['journey']['arrival'] == 1400
    assert len(agent['result']['walking_links']) == 2
    assert context.deps.pending[0].map.region_ids == ('R',)
    assert json.loads(json.dumps(asdict(context.deps.pending[0].map.transit))) == response.json()['map_target']
    assert [point['role'] for point in response.json()['map_target']['points']] == ['origin', 'destination', 'stop', 'stop']
    assert agent['coverage']['snapshot_id'] == 'snapshot'


def test_http_rejects_invalid_departure_before_running_query() -> None:
    service = Mock()
    app = FastAPI()
    app.include_router(build_transit_router(service))
    with TestClient(app) as client:
        response = client.post('/regions/R/transit-journeys', json={'origin_id': 'home', 'facility_id': 'clinic', 'departure_seconds': 86400})
    assert response.status_code == 422
    service.plan.assert_not_called()


def test_unverified_cross_region_clock_chain_is_not_silently_used() -> None:
    service = queries()
    snapshot = service.catalog.latest()
    snapshot.stops.append(TransitStop('X', 'External', 'other', '00', None, None, 'unresolved', '', ''))
    snapshot.connections.extend([TransitConnection('shortcut', 'A', 'X', 100, 200),
                                 TransitConnection('shortcut', 'X', 'B', 250, 300, sequence=1)])
    result = service.plan('R', 'home', 'clinic', 0)
    assert result.result.journey is not None and result.result.journey.arrival == 1400
    assert result.coverage.within_region_connections == 1
    assert result.clock_scope == 'within_region_source_clocks'
