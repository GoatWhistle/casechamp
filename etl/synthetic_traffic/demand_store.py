import json
from dataclasses import asdict
from hashlib import file_digest
from pathlib import Path

import numpy as np
from synthetic_traffic.model import Trip


def save_demand(directory: Path, trips: list[Trip], metadata: dict) -> None:
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    np.savez_compressed(directory / 'trips.npz',
                        origin=np.fromiter((t.origin for t in trips), dtype=np.int64),
                        destination=np.fromiter((t.destination for t in trips), dtype=np.int64),
                        vehicles=np.fromiter((t.vehicles_per_hour for t in trips), dtype=float))
    with (directory / 'trips.npz').open('rb') as stream:
        digest = file_digest(stream, 'sha256').hexdigest()
    (directory / 'demand.json').write_text(json.dumps(
        {'metadata': metadata, 'sha256': digest, 'count': len(trips)}, allow_nan=False))


def load_demand(directory: Path, source: dict, parameters, region_ids):
    record = json.loads((directory / 'demand.json').read_text())
    metadata = record['metadata']
    if (metadata['source'] != source or metadata['parameters'] != asdict(parameters)
            or metadata.get('region_ids') != region_ids):
        raise ValueError('Saved demand sources or parameters do not match')
    with (directory / 'trips.npz').open('rb') as stream:
        if file_digest(stream, 'sha256').hexdigest() != record['sha256']:
            raise ValueError('Saved demand checksum mismatch')
    with np.load(directory / 'trips.npz', allow_pickle=False) as arrays:
        trips = [Trip(int(a), int(b), float(c)) for a, b, c in
                 zip(arrays['origin'], arrays['destination'], arrays['vehicles'], strict=True)]
    if len(trips) != record['count']:
        raise ValueError('Saved demand count mismatch')
    return trips, metadata
