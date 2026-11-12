from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from synthetic_traffic.model import Network

from app.adapter.road_graph.weighted import minimum_csr


class IndexNetwork:
    def __init__(
        self,
        edges: dict[str, Any],
        allowed: Any,
        positions: dict[Any, int],
        count: int,
        network: Network,
        hours: Any,
    ) -> None:
        self.positions, self.count, self.allowed = positions, count, allowed
        self.weight_dtype = edges["h"].dtype
        self.unaffected: dict[tuple[int, int], float] = {}
        pairs = {(min(a, b), max(a, b)) for a, b, _ in positions}
        keys = np.array([a * count + b for a, b in pairs], dtype=np.int64)
        national_keys = np.minimum(edges["src"], edges["dst"]).astype(
            np.int64
        ) * count + np.maximum(edges["src"], edges["dst"])
        selected = np.flatnonzero(np.isin(national_keys, keys) & allowed)
        owned = set(positions.values())
        for raw_position in selected:
            i = int(raw_position)
            if i not in owned:
                a, b = int(edges["src"][i]), int(edges["dst"][i])
                pair = min(a, b), max(a, b)
                self.unaffected[pair] = min(self.unaffected.get(pair, np.inf), float(edges["h"][i]))
        weights = edges["h"].copy()
        for i, way in enumerate(network.way_id):
            if way >= 0:
                a, b = (
                    int(network.raw_nodes[network.source[i]]),
                    int(network.raw_nodes[network.target[i]]),
                )
                weights[positions[a, b, int(way)]] = hours[i]
        valid = np.isfinite(weights) & allowed
        self.base = minimum_csr(edges["src"][valid], edges["dst"][valid], weights[valid], count)
        self.pairs = pairs

    def changed(self, network: Network, hours: Any) -> Any:
        return self.changed_with_delta(network, hours)[0]

    def changed_with_delta(
        self, network: Network, hours: Any
    ) -> tuple[Any, tuple[Any, Any, Any, Any]]:
        values = {pair: self.unaffected.get(pair, np.inf) for pair in self.pairs}
        for i, way in enumerate(network.way_id):
            a, b = (
                int(network.raw_nodes[network.source[i]]),
                int(network.raw_nodes[network.target[i]]),
            )
            if way >= 0 and not self.allowed[self.positions[a, b, int(way)]]:
                continue
            pair = min(a, b), max(a, b)
            if pair not in values:
                start, end = self.base.indptr[a : a + 2]
                position = int(start + np.searchsorted(self.base.indices[start:end], b))
                values[pair] = (
                    float(self.base.data[position])
                    if position < end and self.base.indices[position] == b
                    else np.inf
                )
            values[pair] = min(values[pair], float(np.asarray(hours[i], dtype=self.weight_dtype)))
        sources, targets, previous, updated = [], [], [], []
        replacements = []
        new_a, new_b, new_w = [], [], []
        for (a, b), value in values.items():
            for source, target in ((a, b), (b, a)):
                start, end = self.base.indptr[source : source + 2]
                position = int(start + np.searchsorted(self.base.indices[start:end], target))
                present = position < end and self.base.indices[position] == target
                old = float(self.base.data[position]) if present else np.inf
                if old == value:
                    continue
                sources.append(source)
                targets.append(target)
                previous.append(old)
                updated.append(value)
                if present:
                    replacements.append((position, value))
                elif np.isfinite(value):
                    new_a.append(source)
                    new_b.append(target)
                    new_w.append(value)
        delta = (
            np.asarray(sources, dtype=np.int64),
            np.asarray(targets, dtype=np.int64),
            np.asarray(previous, dtype=np.float64),
            np.asarray(updated, dtype=np.float64),
        )
        if not sources:
            return self.base, delta
        result = self.base.copy()
        for position, value in replacements:
            result.data[position] = value
        if new_w:
            order = sorted(range(len(new_a)), key=lambda i: (new_a[i], new_b[i]))
            inserts = []
            for i in order:
                start, end = result.indptr[new_a[i] : new_a[i] + 2]
                inserts.append(int(start + np.searchsorted(result.indices[start:end], new_b[i])))
            data = np.insert(result.data, inserts, [new_w[i] for i in order])
            indices = np.insert(result.indices, inserts, [new_b[i] for i in order])
            indptr = result.indptr.copy()
            indptr[1:] += np.cumsum(np.bincount(new_a, minlength=self.count))
            result = csr_matrix((data, indices, indptr), shape=result.shape)
        return result, delta
