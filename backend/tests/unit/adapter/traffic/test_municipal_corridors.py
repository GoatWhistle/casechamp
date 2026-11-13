from pathlib import Path
from typing import Literal
from unittest.mock import Mock

import numpy as np
import pytest
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.model import Network
from tests.unit.adapter.traffic.test_municipal_scenarios import Store

from app.adapter.traffic.municipal_corridors import municipal_corridors
from app.adapter.traffic.municipal_scenarios import MunicipalScenarioJobs
from app.domain.errors import InvalidQuery
from app.usecase.municipal_scenarios import MunicipalScenarioRequest, MunicipalTrafficCorridor


def test_proposals_prioritize_supported_connected_roads_and_keep_closure_choices() -> None:
    network = Network(
        np.array([0, 1, 2, 4, 6, 8]), np.array([1, 0, 3, 5, 7, 9]),
        np.ones(6), np.full(6, 50.), np.ones(6), np.array([10, 10, 20, 20, 30, 40]),
        np.arange(10), np.zeros(10), np.zeros(10), np.array([-1, -1, -1, -1, 0, -1]),
    )
    flow = np.array([100., 100., 1000., 1000., 100., 0.])
    assignment = Assignment(flow, np.ones(6), flow / 50, float(flow.sum()), 0, 0, 1, True, [])
    rows = municipal_corridors(network, assignment, list(range(6)), {10: 'Connected road'})
    assert [row.way_id for row in rows] == [10, 20, 30, 40]
    assert rows[0].capacity_eligible and rows[0].name == 'Connected road'
    assert rows[0].length_km == 1
    assert rows[1].capacity_reason == 'disconnected_segments'
    assert rows[1].connected_parts == 2
    assert rows[2].capacity_reason == 'shared_lane'
    assert rows[3].capacity_reason == 'no_assigned_demand'
    assert all(not row.capacity_eligible for row in rows[1:])
    local = municipal_corridors(network, assignment, [2], {})
    assert local[0].way_id == 20 and local[0].capacity_eligible


def test_unsupported_capacity_is_rejected_before_creating_a_job(tmp_path: Path) -> None:
    directory = tmp_path / 'published'
    directory.mkdir()
    (directory / 'sha256').write_text('test')
    baselines = Mock()
    baselines.get.return_value.baseline_id = 'published'
    baselines.get.return_value.corridors = [MunicipalTrafficCorridor(
        10, 3., 100., 2., capacity_eligible=False, capacity_reason='disconnected_segments', connected_parts=2,
    )]
    store = Store()
    jobs = MunicipalScenarioJobs(tmp_path, store, baselines=baselines)
    try:
        with pytest.raises(InvalidQuery, match='lane-addition'):
            jobs.submit(MunicipalScenarioRequest('published', 'R', 'M', 'capacity', [10]))
        assert store.items == {}
    finally:
        jobs.close()


@pytest.mark.parametrize(('kind', 'connected', 'accepted'), [
    ('capacity', False, False), ('capacity', True, True), ('closure', False, True),
])
def test_combined_selection_checks_connectivity_before_job_creation(
    tmp_path: Path, kind: Literal["capacity", "closure"], connected: bool, accepted: bool,
) -> None:
    directory = tmp_path / 'published'
    directory.mkdir()
    (directory / 'sha256').write_text('test')
    network = Network(
        np.array([0, 1 if connected else 2]), np.array([1, 3]),
        np.ones(2), np.full(2, 50.), np.ones(2), np.array([10, 20]),
        np.arange(4), np.zeros(4), np.zeros(4), np.full(2, -1),
    )
    baselines = Mock()
    baselines.get.return_value.baseline_id = 'published'
    baselines.get.return_value.corridors = [MunicipalTrafficCorridor(way, 1., 100., 1.) for way in [10, 20]]
    baselines.load.return_value.network = network
    baselines.selected_edges.return_value = [0, 1]
    store = Store()
    jobs = MunicipalScenarioJobs(tmp_path, store, baselines=baselines)
    jobs.pool.shutdown()
    executor = Mock()
    jobs.pool = executor
    request = MunicipalScenarioRequest('published', 'R', 'M', kind, [10, 20])
    try:
        if accepted:
            result = jobs.submit(request)
            assert result.id in store.items
            executor.submit.assert_called_once()
        else:
            with pytest.raises(InvalidQuery, match='contiguous corridor'):
                jobs.submit(request)
            assert store.items == {}
            executor.submit.assert_not_called()
    finally:
        jobs.close()
