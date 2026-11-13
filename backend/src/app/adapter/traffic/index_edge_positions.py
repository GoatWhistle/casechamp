from typing import Any

import numpy as np
from synthetic_traffic.model import Network

from app.domain.errors import InvalidQuery


def traffic_edge_positions(
    edges: dict[str, Any], network: Network, ways: dict[int, int], count: int,
) -> Any:
    way_ids = np.array(sorted(ways), dtype=np.int64)
    way_indices = np.array([ways[int(way)] for way in way_ids], dtype=np.int64)
    keys = np.empty(len(edges['src']), dtype=[('pair', '<i8'), ('way', '<i8')])
    keys['pair'] = edges['src'].astype(np.int64) * count + edges['dst']
    keys['way'] = edges['way_idx']
    order = np.argsort(keys, kind='stable')
    keys = keys[order]
    result = np.full(len(network.source), -1, dtype=np.int64)
    for start in range(0, len(result), 200_000):
        end = min(start + 200_000, len(result))
        selected = np.flatnonzero(network.way_id[start:end] >= 0) + start
        if not len(selected):
            continue
        ids = network.way_id[selected]
        location = np.searchsorted(way_ids, ids)
        if np.any(location >= len(way_ids)) or np.any(way_ids[location] != ids):
            raise InvalidQuery('Traffic road identity differs from the index graph')
        query = np.empty(len(selected), dtype=keys.dtype)
        query['pair'] = network.raw_nodes[network.source[selected]] * count + network.raw_nodes[network.target[selected]]
        query['way'] = way_indices[location]
        position = np.searchsorted(keys, query, side='right') - 1
        if np.any(position < 0) or np.any(keys[position] != query):
            raise InvalidQuery('Traffic edge identity differs from the index graph')
        result[selected] = order[position]
    return result


def pair_keys(source: Any, target: Any, count: int, directed: bool) -> Any:
    if directed:
        return np.asarray(source, dtype=np.int64) * count + target
    return np.minimum(source, target).astype(np.int64) * count + np.maximum(source, target)


def parallel_floor(edges: dict[str, Any], allowed: Any, owned: Any, keys: Any,
                   count: int, directed: bool) -> Any:
    selected = allowed.copy()
    selected[owned] = False
    result = np.full(len(keys), np.inf)
    if not len(keys):
        return result
    for start in range(0, len(selected), 200_000):
        indices = np.flatnonzero(selected[start:start + 200_000]) + start
        query = pair_keys(edges['src'][indices], edges['dst'][indices], count, directed)
        positions = np.searchsorted(keys, query)
        valid = positions < len(keys)
        valid[valid] &= keys[positions[valid]] == query[valid]
        np.minimum.at(result, positions[valid], edges['h'][indices[valid]])
    return result
