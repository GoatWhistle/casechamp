from dataclasses import replace

import numpy as np

from synthetic_traffic.model import Network


def close_lane(network: Network, selected: np.ndarray) -> Network:
    if int(selected.sum()) != 1:
        raise ValueError('Lane closure requires one directed road segment')
    if np.any(network.shared[selected] >= 0):
        raise ValueError('A shared lane cannot be closed in only one direction')
    lanes = network.capacity[selected] / 1800
    if not np.allclose(lanes, np.round(lanes), rtol=0, atol=1e-8):
        raise ValueError('Lane closure requires capacity based on whole 1800-PCU lanes')
    capacity = network.capacity.copy()
    capacity[selected] -= 1800
    keep = capacity > 0
    if not keep.any():
        raise ValueError('Closure cannot remove every network edge')
    fields = {name: getattr(network, name)[keep] for name in (
        'source', 'target', 'free_hours', 'length_km', 'way_id', 'shared',
    )}
    return replace(network, capacity=capacity[keep], **fields)
