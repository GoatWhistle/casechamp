import json
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from synthetic_traffic.load_preview import digest, load_preview, save_preview
from synthetic_traffic.source import load_network
from tests.unit.adapter.traffic.snapshot_fixture import snapshot

from app.adapter.traffic.municipal_baselines import MunicipalBaselines
from app.domain.errors import DataUnavailable
from app.usecase.municipal_improvement import propose_lane
from app.usecase.municipal_scenarios import MunicipalTrafficBaseline
from app.usecase.traffic import TrafficJob, TrafficScope


def test_preview_round_trip_keeps_real_gap_and_rejects_corruption(tmp_path: Path) -> None:
    source = tmp_path
    snapshot(source)
    (source / 'source.json').write_text(json.dumps({'sha256': {
        name: digest(source / name) for name in ['edges.parquet', 'nodes.parquet']}}))
    graph = load_network(source)
    destination = tmp_path / 'published'
    flow = np.ones(len(graph.source))
    save_preview(destination, source, flow, .015, {'region_ids': ['region']}, {'unserved_vehicles_per_hour': 5.})
    loaded = load_preview(destination)
    np.testing.assert_array_equal(loaded.assignment.flow, flow)
    assert loaded.assignment.relative_gap == .015
    assert loaded.assignment.converged is False
    assert loaded.assignment.unserved_vehicles_per_hour == 5.
    assert loaded.assignment.vehicle_hours_per_hour > 0
    (destination / 'flow.npz').write_bytes(b'broken')
    with pytest.raises(ValueError, match='checksum'):
        load_preview(destination)


def test_improvement_waits_for_routing_state_even_when_preview_is_published() -> None:
    scenarios = Mock()
    scenarios.baseline.return_value = MunicipalTrafficBaseline('preview', 'district', [], [],
        .015, None, 'sha', TrafficJob('preview', TrafficScope(), stage='preliminary'))
    result, job = propose_lane(scenarios, 'region', 'district')
    assert result['status'] == 'awaiting_routing_baseline'
    assert job is None
    scenarios.submit.assert_not_called()


def test_catalog_tries_lower_gap_before_old_preview(tmp_path: Path) -> None:
    for name, gap in [('z-preview', .015), ('a-refined', .001)]:
        directory = tmp_path / name
        directory.mkdir()
        (directory / 'sha256').write_text('sha')
        (directory / 'state.json').write_text(json.dumps({'assignment': {'relative_gap': gap}}))
    boundaries = Mock()
    municipality = Mock()
    municipality.id = 'district'
    municipality.coordinates = [[[(40., 44.), (41., 45.)]]]
    boundaries.run.return_value.items = [municipality]
    catalog = MunicipalBaselines(tmp_path, boundaries)
    with patch.object(catalog, 'load', side_effect=DataUnavailable('Stop after selected candidate')) as load:
        with pytest.raises(DataUnavailable):
            catalog.get('region', 'district')
        load.assert_called_once_with('a-refined')
