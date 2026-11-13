import numpy as np
from synthetic_traffic.model import Network


def edge_keys(network: Network, start: int = 0, end: int | None = None) -> np.ndarray:
    selected = slice(start, end)
    keys = np.empty(len(network.source[selected]), dtype=[('pair', '<i8'), ('way', '<i8')])
    keys['pair'] = network.source[selected] * len(network.raw_nodes) + network.target[selected]
    keys['way'] = network.way_id[selected]
    return keys


def align_edges(source: Network, requested: Network, chunk_size: int = 200_000) -> np.ndarray:
    if not np.array_equal(source.raw_nodes, requested.raw_nodes):
        raise ValueError('Edge alignment requires matching node identities and order')
    if chunk_size < 1:
        raise ValueError('Edge alignment chunk size must be positive')
    keys = edge_keys(source)
    order = np.argsort(keys, kind='stable')
    keys = keys[order]
    result = np.full(len(requested.source), -1, dtype=np.int64)
    for start in range(0, len(result), chunk_size):
        query = edge_keys(requested, start, start + chunk_size)
        position = np.searchsorted(keys, query, side='right') - 1
        valid = position >= 0
        valid[valid] &= keys[position[valid]] == query[valid]
        chunk = result[start:start + chunk_size]
        chunk[valid] = order[position[valid]]
    return result
