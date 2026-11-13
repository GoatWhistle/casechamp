import json
from dataclasses import asdict, replace
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.usecase.test_municipal_indices import Source

from app.adapter.chat.municipal_tools import MunicipalTools
from app.controller.municipalities.indices import build_municipal_indices_router
from app.domain.errors import InvalidQuery
from app.domain.normative.index import IndexValue
from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_indices import MunicipalIndexQueries
from app.usecase.municipal_overview import municipal_overview
from app.usecase.municipal_service_models import MunicipalNormativeValue
from app.usecase.municipal_service_priority import service_priority
from app.usecase.municipal_services import MunicipalServiceQueries
from app.usecase.municipalities import Municipality, MunicipalityQueries


def service(within: int, measured: int) -> MunicipalNormativeValue:
    policy = scenario_policy('N04')
    return MunicipalNormativeValue('N04', status='available', definition_sha256=policy.definition_sha256,
        unit=policy.unit, thresholds=policy.thresholds,
        values=(IndexValue(policy.thresholds[0], 100, measured, within, 100 - measured,
                           float(within), None, None, None),))


def test_deficit_bounds_keep_missing_measurements_out_of_confirmed_harm() -> None:
    value = service_priority('N04', [service(10, 30)])
    assert value.confirmed_deficit_points == 20
    assert value.confirmed_deficit_percent == 20
    assert value.possible_deficit_percent == 90
    assert value.unresolved_points == 70
    assert service_priority('N04', [service(0, 0)]).status == 'unavailable'
    assert service_priority('N04', [replace(service(10, 30), definition_sha256='stale')]).status == 'unavailable'


def queries() -> MunicipalIndexQueries:
    districts = [Municipality(name, '07000000', name, 6,
                  [[[(40, 44), (41, 44), (41, 45), (40, 45), (40, 44)]]],
                  'https://source', '2026-11-13', 'hash', 'polygon', 1.)
                 for name in ('unknown', 'partial', 'confirmed')]
    rows = {'unknown': service(0, 0), 'partial': service(10, 30), 'confirmed': service(40, 100)}
    municipalities = cast(MunicipalityQueries, SimpleNamespace(run=lambda region: SimpleNamespace(items=districts)))
    services = cast(MunicipalServiceQueries, SimpleNamespace(published=lambda district: [rows[district.id]], published_overview=None))
    return MunicipalIndexQueries(municipalities, Source(), services)


def test_agent_and_http_share_service_ranking_and_selected_season() -> None:
    source = queries()
    assert source.services is not None
    expected = municipal_overview('07000000', source.municipalities, source.repository, 'N04',
                                  source.services.published, 'winter')
    assert [item.municipality_id for item in expected.items] == ['confirmed', 'partial', 'unknown']
    assert expected.season == 'winter'
    agent = json.loads(MunicipalTools(source, None).municipal_analysis(
        Mock(), 'overview', region_id='07000000', criterion_id='N04', season='winter',
    ))
    app = FastAPI()
    app.include_router(build_municipal_indices_router(source))
    response = TestClient(app).get('/regions/07000000/municipalities-overview',
                                   params={'criterion_id': 'N04', 'season': 'winter'})
    assert response.status_code == 200
    assert response.json() == agent == asdict(expected)
    with pytest.raises(InvalidQuery):
        municipal_overview('07000000', source.municipalities, source.repository, 'N99')
