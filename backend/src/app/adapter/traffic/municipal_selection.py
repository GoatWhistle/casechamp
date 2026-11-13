import numpy as np
from synthetic_traffic.incremental import IncrementalBaseline

from app.domain.errors import InvalidQuery
from app.usecase.municipal_scenarios import MunicipalScenarioRequest


def select_edges(request: MunicipalScenarioRequest, baseline: IncrementalBaseline,
                 municipal_edges: list[int]) -> list[int]:
    if request.kind == 'lane_closure' and len(request.edge_indices) != 1:
        raise InvalidQuery('Choose one directed road segment for lane closure')
    if not request.edge_indices:
        return municipal_edges
    if len(set(request.edge_indices)) != len(request.edge_indices):
        raise InvalidQuery('Road segment selection must not contain duplicates')
    if not set(request.edge_indices).issubset(municipal_edges):
        raise InvalidQuery('Selected segments must belong to the municipality and roads')
    selected = np.array(request.edge_indices, dtype=np.int64)
    if request.kind == 'lane_closure' and np.any(baseline.network.shared[selected] >= 0):
        raise InvalidQuery('A shared lane cannot be closed in only one direction')
    return request.edge_indices
