import json

import numpy as np
import pytest
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.incremental_paths import PathCache
from synthetic_traffic.initial_flow_checkpoint import (
    feasible_initial_flow,
    read_initial_flows,
)
from synthetic_traffic.model import Trip
from synthetic_traffic.origin_flows import current_flows
from synthetic_traffic.origin_snapshot import digest
from synthetic_traffic.origin_store import OriginStore
from test_traffic_incremental import network


def test_resume_from_initial_flows_matches_fresh_congested_assignment(tmp_path):
    graph = network()
    trips = [Trip(0, 4, 20.), Trip(4, 3, 4.), Trip(2, 1, 3.)]
    paths = PathCache(graph, trips, graph.free_hours)
    paths.load(graph)
    initial = dict(current_flows(paths))
    expected = prepare_incremental(graph, trips, iterations=25, path_limit=3.)
    resumed = prepare_incremental(graph, trips, iterations=25, path_limit=3.,
                                  tree_directory=tmp_path / 'trees', initial_flows=initial)
    np.testing.assert_allclose(resumed.assignment.flow, expected.assignment.flow)
    np.testing.assert_allclose(resumed.assignment.hours, expected.assignment.hours)
    assert resumed.assignment.od_hours == pytest.approx(expected.assignment.od_hours)
    assert resumed.assignment.relative_gap == pytest.approx(expected.assignment.relative_gap)
    assert resumed.assignment.iterations == expected.assignment.iterations


def test_resume_refuses_infeasible_flow_before_replacing_tree_cache(tmp_path):
    graph = network()
    tree_dir = tmp_path / 'trees'
    tree_dir.mkdir()
    marker = tree_dir / '0.npz'
    marker.write_bytes(b'original')
    with pytest.raises(ValueError, match='conservation'):
        prepare_incremental(graph, [Trip(0, 4, 20.)], tree_directory=tree_dir,
                            initial_flows={0: {0: 1.}})
    assert marker.read_bytes() == b'original'
    with pytest.raises(ValueError, match='origins'):
        feasible_initial_flow(graph, [Trip(0, 4, 20.)], {})


def test_flow_checkpoint_rejects_changed_source_demand_and_bytes(tmp_path):
    store = OriginStore(tmp_path / 'flows', 'flows')
    store[0] = {0: 1.}
    record = {'stage': 'before_first_assignment_iteration', 'source': {'revision': 'one'},
              'demand_sha256': 'demand', 'flows': {'0': digest(store.directory / '0.npz')}}
    (tmp_path / 'checkpoint.json').write_text(json.dumps(record))
    assert read_initial_flows(tmp_path, record['source'], 'demand')[0] == {0: 1.}
    record['stage'] = 'feasible_warm_start'
    (tmp_path / 'checkpoint.json').write_text(json.dumps(record))
    assert read_initial_flows(tmp_path, record['source'], 'demand')[0] == {0: 1.}
    for source, demand in [({'revision': 'two'}, 'demand'), (record['source'], 'changed')]:
        with pytest.raises(ValueError, match='match'):
            read_initial_flows(tmp_path, source, demand)
    store[0] = {0: 2.}
    with pytest.raises(ValueError, match='checksum'):
        read_initial_flows(tmp_path, record['source'], 'demand')
