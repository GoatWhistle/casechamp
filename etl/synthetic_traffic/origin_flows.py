from collections.abc import Mapping, MutableMapping

import numpy as np
from synthetic_traffic.edge_identity import align_edges
from synthetic_traffic.incremental_paths import PathCache
from synthetic_traffic.model import Network

OriginFlows = MutableMapping[int, dict[int, float]]


class CurrentFlows(Mapping):
    def __init__(self, paths):
        self.paths = paths

    def __iter__(self):
        return iter(self.paths.loads)

    def __len__(self):
        return len(self.paths.loads)

    def __getitem__(self, origin):
        amounts, _, _ = self.paths.loads[origin]
        indices = self.paths.edges.edge_ids(amounts)
        return dict(zip(map(int, indices), amounts.values(), strict=True))


def current_flows(paths: PathCache) -> Mapping[int, dict[int, float]]:
    return CurrentFlows(paths)


def blend_flows(flows: OriginFlows, auxiliary: Mapping[int, dict[int, float]], weight: float) -> None:
    for origin, values in auxiliary.items():
        previous = flows[origin]
        flows[origin] = {
            edge: previous.get(edge, 0.0) * (1 - weight) + values.get(edge, 0.0) * weight
            for edge in previous.keys() | values.keys()
        }


class RemappedFlows(Mapping):
    def __init__(self, mapping, flows, auxiliary):
        self.mapping, self.flows, self.auxiliary = mapping, flows, auxiliary

    def __iter__(self):
        return iter(self.flows)

    def __len__(self):
        return len(self.flows)

    def __getitem__(self, origin):
        values = self.flows[origin]
        if any(self.mapping[edge] < 0 and amount > 0 for edge, amount in values.items()):
            return self.auxiliary[origin]
        return {int(self.mapping[edge]): amount for edge, amount in values.items()
                if self.mapping[edge] >= 0}


def remap_flows(
    original: Network,
    changed: Network,
    flows: OriginFlows,
    paths: PathCache,
) -> tuple[np.ndarray, Mapping[int, dict[int, float]]]:
    mapping = align_edges(changed, original)
    result = RemappedFlows(mapping, flows, current_flows(paths))
    total = np.zeros(len(changed.source))
    for selected in result.values():
        for edge, amount in selected.items():
            total[edge] += amount
    return total, result
