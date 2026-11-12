from itertools import pairwise

import numpy as np
from synthetic_traffic.incremental_paths import checkpoint


def changes(before, after, deadline=None):
    sources, targets, old, new = [], [], [], []
    count = before.shape[0]
    for start in range(0, count, 32768):
        checkpoint(deadline)
        end = min(start + 32768, count)
        before_left, before_right = before.indptr[start], before.indptr[end]
        after_left, after_right = after.indptr[start], after.indptr[end]
        if (
            np.array_equal(
                before.indptr[start : end + 1] - before_left,
                after.indptr[start : end + 1] - after_left,
            )
            and np.array_equal(
                before.indices[before_left:before_right],
                after.indices[after_left:after_right],
            )
            and np.array_equal(
                before.data[before_left:before_right],
                after.data[after_left:after_right],
            )
        ):
            continue
        keys = []
        weights = []
        for graph in (before, after):
            left, right = graph.indptr[start], graph.indptr[end]
            rows = np.repeat(
                np.arange(start, end, dtype=np.int64),
                np.diff(graph.indptr[start : end + 1]),
            )
            keys.append(rows * count + graph.indices[left:right])
            weights.append(graph.data[left:right])
        union = np.union1d(*keys)
        values = []
        for key, weight in zip(keys, weights, strict=True):
            value = np.full(len(union), np.inf)
            value[np.searchsorted(union, key)] = weight
            values.append(value)
        selected = values[0] != values[1]
        changed = union[selected]
        sources.append(changed // count)
        targets.append(changed % count)
        old.append(values[0][selected])
        new.append(values[1][selected])
    if not sources:
        return (np.empty(0, dtype=np.int64),) * 2 + (np.empty(0),) * 2
    return tuple(np.concatenate(a) for a in (sources, targets, old, new))


def edge_values(graph, source, target):
    values = np.full(len(source), np.inf)
    order = np.argsort(source, kind="stable")
    sorted_source = source[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_source)) + 1, len(order)]
    for left, right in pairwise(starts):
        if left == right:
            continue
        selected = order[left:right]
        row = int(source[selected[0]])
        begin, end = graph.indptr[row : row + 2]
        indices = graph.indices[begin:end]
        positions = np.searchsorted(indices, target[selected])
        found = positions < len(indices)
        if not len(indices):
            continue
        found &= indices[np.minimum(positions, len(indices) - 1)] == target[selected]
        values[selected[found]] = graph.data[begin + positions[found]]
    return values


def validated_delta(before, after, delta):
    if len(delta) != 4:
        raise ValueError("Sparse graph delta requires source,target,old,new arrays")
    source, target, old, new = (np.asarray(values) for values in delta)
    if any(
        values.ndim != 1 or len(values) != len(source)
        for values in (source, target, old, new)
    ):
        raise ValueError("Sparse graph delta arrays must align")
    if not all(np.issubdtype(values.dtype, np.integer) for values in (source, target)):
        raise TypeError("Sparse graph delta endpoints must be integer arrays")
    source, target = (
        source.astype(np.int64, copy=False),
        target.astype(np.int64, copy=False),
    )
    old, new = old.astype(np.float64, copy=False), new.astype(np.float64, copy=False)
    if (
        np.any(source < 0)
        or np.any(target < 0)
        or np.any(source >= before.shape[0])
        or np.any(target >= before.shape[0])
    ):
        raise ValueError("Sparse graph delta endpoints are outside the graph")
    if np.isnan(old).any() or np.isnan(new).any() or np.any(old < 0) or np.any(new < 0):
        raise ValueError(
            "Sparse graph delta weights must be nonnegative or positive infinity"
        )
    if len(np.unique(source * before.shape[0] + target)) != len(source):
        raise ValueError("Sparse graph delta must contain each directed pair once")
    if not np.array_equal(
        edge_values(before, source, target), old
    ) or not np.array_equal(edge_values(after, source, target), new):
        raise ValueError(
            "Sparse graph delta weights do not match the changed edge pairs"
        )
    changed = old != new
    return source[changed], target[changed], old[changed], new[changed]


def tree_impact(tree, delta, horizon):
    source, target, old, new = delta
    nodes = np.unique(np.r_[source, target])
    values = tree.distance[nodes]
    before = values[np.searchsorted(nodes, source)]
    after = values[np.searchsorted(nodes, target)]
    proposals = before + new
    decrease = bool(np.any((new < old) & (proposals < after) & (proposals <= horizon)))
    raised = np.flatnonzero((new > old) & (after <= horizon))
    increase = bool(
        len(raised) and np.any(tree.parent[target[raised]] == source[raised])
    )
    return decrease or increase, increase
