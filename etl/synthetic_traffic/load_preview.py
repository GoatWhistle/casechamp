import json
import os
import shutil
from dataclasses import dataclass
from hashlib import file_digest, sha256
from pathlib import Path
from uuid import uuid4

import numpy as np
from synthetic_traffic.assignment import Assignment, costs
from synthetic_traffic.model import Network
from synthetic_traffic.source import load_network


@dataclass
class LoadPreview:
    network: Network
    assignment: Assignment


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def save_preview(destination: Path, snapshot: Path, flow: np.ndarray, gap: float,
                 metadata: dict, evidence: dict) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    if not np.isfinite(gap) or gap < 0 or np.any(~np.isfinite(flow)) or np.any(flow < 0):
        raise ValueError('Preview requires finite nonnegative flow and measured gap')
    source = json.loads((snapshot / 'source.json').read_text())
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + '.' + uuid4().hex)
    staging.mkdir()
    try:
        np.savez_compressed(staging / 'flow.npz', flow=flow)
        record = {'schema': 'load_preview_v1', 'preview': True,
                  'snapshot': str(snapshot.resolve()), 'source': source,
                  'metadata': metadata, 'evidence': evidence,
                  'assignment': {'relative_gap': gap, 'converged': False},
                  'flow_sha256': digest(staging / 'flow.npz')}
        payload = json.dumps(record, allow_nan=False, separators=(',', ':'))
        (staging / 'state.json').write_text(payload)
        (staging / 'sha256').write_text(sha256(payload.encode()).hexdigest())
        os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def load_preview(directory: Path) -> LoadPreview:
    payload = (directory / 'state.json').read_bytes()
    if sha256(payload).hexdigest() != (directory / 'sha256').read_text():
        raise ValueError('Preview manifest checksum mismatch')
    record = json.loads(payload)
    if record.get('schema') != 'load_preview_v1' or not record.get('preview'):
        raise ValueError('Not a load preview')
    if digest(directory / 'flow.npz') != record['flow_sha256']:
        raise ValueError('Preview flow checksum mismatch')
    snapshot = Path(record['snapshot'])
    for name, expected in record['source']['sha256'].items():
        if digest(snapshot / name) != expected:
            raise ValueError('Preview graph snapshot checksum mismatch')
    network = load_network(snapshot)
    with np.load(directory / 'flow.npz', allow_pickle=False) as arrays:
        flow = arrays['flow']
    if flow.shape != network.capacity.shape or np.any(~np.isfinite(flow)) or np.any(flow < 0):
        raise ValueError('Invalid preview flow')
    hours, ratio = costs(network, flow)
    return LoadPreview(network, Assignment(flow, hours, ratio, float(flow @ hours),
        float(record['evidence'].get('unserved_vehicles_per_hour', 0.)),
        float(record['assignment']['relative_gap']), 1, False, []))
