from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from synthetic_traffic.edge_identity import align_edges
from synthetic_traffic.model import Network

from app.adapter.road_graph.weighted import minimum_csr
from app.adapter.traffic.index_edge_positions import pair_keys, parallel_floor


class IndexNetwork:
    def __init__(
        self, edges: dict[str, Any], allowed: Any, positions: Any, count: int,
        network: Network, hours: Any, directed: bool = False,
    ) -> None:
        self.directed = directed
        self.positions, self.count, self.allowed = positions, count, allowed
        self.original = network
        self.weight_dtype = edges['h'].dtype
        present = positions >= 0
        owned = np.unique(positions[present])
        self.pairs = np.unique(pair_keys(network.raw_nodes[network.source[present]],
                                        network.raw_nodes[network.target[present]], count, directed))
        self.unaffected = parallel_floor(edges, allowed, owned, self.pairs, count, directed)
        weights = edges['h'].copy()
        weights[positions[present]] = np.asarray(hours)[present]
        valid = np.isfinite(weights) & allowed
        self.base = minimum_csr(edges['src'][valid], edges['dst'][valid], weights[valid], count, directed=directed)
        self.base_keys = np.repeat(np.arange(count, dtype=np.int64), np.diff(self.base.indptr)) * count + self.base.indices

    def changed(self, network: Network, hours: Any) -> Any:
        return self.changed_with_delta(network, hours)[0]

    def _values(self, network: Network, hours: Any) -> tuple[Any, Any]:
        mapping = align_edges(self.original, network)
        real = network.way_id >= 0
        if np.any(real & (mapping < 0)):
            raise ValueError('Scenario road is absent from the baseline index network')
        selected = ~real
        real_indices = np.flatnonzero(real)
        selected[real_indices] = self.allowed[self.positions[mapping[real_indices]]]
        query = pair_keys(network.raw_nodes[network.source[selected]],
                          network.raw_nodes[network.target[selected]], self.count, self.directed)
        keys = np.union1d(self.pairs, query)
        values = np.full(len(keys), np.inf)
        positions = np.searchsorted(keys, self.pairs)
        values[positions] = self.unaffected
        extra = np.ones(len(keys), dtype=bool)
        extra[positions] = False
        _, previous = self._lookup(keys[extra])
        values[extra] = previous
        np.minimum.at(values, np.searchsorted(keys, query), np.asarray(hours, dtype=self.weight_dtype)[selected])
        return keys, values

    def _lookup(self, keys: Any) -> tuple[Any, Any]:
        positions = np.searchsorted(self.base_keys, keys)
        valid = positions < len(self.base_keys)
        valid[valid] &= self.base_keys[positions[valid]] == keys[valid]
        values = np.full(len(keys), np.inf)
        values[valid] = self.base.data[positions[valid]]
        return positions, values

    def changed_with_delta(self, network: Network, hours: Any) -> tuple[Any, tuple[Any, Any, Any, Any]]:
        keys, values = self._values(network, hours)
        if not self.directed:
            reverse = keys % self.count * self.count + keys // self.count
            different = reverse != keys
            keys, values = np.r_[keys, reverse[different]], np.r_[values, values[different]]
        order = np.argsort(keys)
        keys, values = keys[order], values[order]
        positions, previous = self._lookup(keys)
        changed = previous != values
        keys, values, positions, previous = (item[changed] for item in (keys, values, positions, previous))
        source, target = keys // self.count, keys % self.count
        delta = source, target, previous, values
        if not len(keys):
            return self.base, delta
        result = self.base.copy()
        present = positions < len(self.base_keys)
        present[present] &= self.base_keys[positions[present]] == keys[present]
        result.data[positions[present]] = values[present]
        added = ~present & np.isfinite(values)
        if np.any(added):
            data = np.insert(result.data, positions[added], values[added])
            indices = np.insert(result.indices, positions[added], target[added])
            indptr = result.indptr.copy()
            indptr[1:] += np.cumsum(np.bincount(source[added], minlength=self.count))
            result = csr_matrix((data, indices, indptr), shape=result.shape)
        return result, delta
