import numpy as np
import pytest
from synthetic_traffic.baseline_store import load_baseline, save_baseline
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import Trip
from synthetic_traffic.origin_store import OriginStore
from test_traffic_incremental import network


def test_disk_origin_records_survive_publication_and_are_immutable(tmp_path):
    baseline = prepare_incremental(network(), [Trip(0, 4, 1.), Trip(2, 3, 1.)],
                                   tree_directory=tmp_path / 'working' / 'trees', path_limit=4.)
    assert isinstance(baseline.paths.loads, OriginStore)
    assert isinstance(baseline.origin_flows, OriginStore)
    save_baseline(baseline, tmp_path / 'published')
    restored = load_baseline(tmp_path / 'published')
    np.testing.assert_array_equal(restored.assignment.flow, baseline.assignment.flow)
    assert restored.origin_flows[0] == baseline.origin_flows[0]
    with pytest.raises(TypeError, match='immutable'):
        restored.origin_flows[0] = {}
    original = restored.paths.loads[0]
    fork = restored.paths.loads.copy()
    fork.pop(0)
    assert 0 not in fork
    assert restored.paths.loads[0] == original
    fork[0] = ({}, 1., {})
    assert restored.paths.loads[0] == original
    (tmp_path / 'published' / 'origins' / 'flows' / '0.npz').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='checksum'):
        load_baseline(tmp_path / 'published')
