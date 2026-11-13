from dataclasses import asdict

import pytest
from synthetic_traffic.demand_store import load_demand, save_demand
from synthetic_traffic.model import DemandParameters, Trip


def test_saved_demand_roundtrips_and_rejects_other_scope(tmp_path):
    parameters = DemandParameters()
    source = {'sha256': {'edges.parquet': 'test'}}
    metadata = {'source': source, 'parameters': asdict(parameters), 'region_ids': ['03', '07']}
    trips = [Trip(1, 2, 12.5), Trip(2, 1, 8.)]
    save_demand(tmp_path / 'demand', trips, metadata)
    restored, actual = load_demand(tmp_path / 'demand', source, parameters, ['03', '07'])
    assert restored == trips
    assert actual == metadata
    with pytest.raises(ValueError, match='sources or parameters'):
        load_demand(tmp_path / 'demand', source, parameters, ['03'])
    with pytest.raises(FileExistsError):
        save_demand(tmp_path / 'demand', trips, metadata)


def test_saved_demand_rejects_corrupt_arrays(tmp_path):
    parameters = DemandParameters()
    metadata = {'source': {}, 'parameters': asdict(parameters), 'region_ids': None}
    save_demand(tmp_path / 'demand', [Trip(1, 2, 1.)], metadata)
    (tmp_path / 'demand' / 'trips.npz').write_bytes(b'broken')
    with pytest.raises(ValueError, match='checksum'):
        load_demand(tmp_path / 'demand', {}, parameters, None)
