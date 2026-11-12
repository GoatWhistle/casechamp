from heapq import heappop, heappush
from time import monotonic

import numpy as np
from numba import njit, objmode
from synthetic_traffic.incremental_paths import checkpoint


@njit(cache=True)
def _check(deadline):
    if np.isfinite(deadline):
        with objmode(expired="boolean"):
            expired = monotonic() >= deadline
        if expired:
            raise TimeoutError("Index repair deadline reached")


@njit(cache=True, nogil=True)
def _kernel(
    indptr,
    indices,
    weights,
    reverse_ptr,
    reverse_indices,
    reverse_weights,
    distance,
    parent,
    source,
    target,
    old,
    new,
    deadline,
    horizon,
):
    _check(deadline)
    increased = np.empty(len(source), dtype=np.int32)
    decreased = np.empty(len(source), dtype=np.int32)
    increase_count, decrease_count, operations = 0, 0, 0
    for i in range(len(source)):
        if (
            parent[target[i]] == source[i]
            and new[i] > old[i]
            and distance[target[i]] <= horizon
        ):
            increased[increase_count] = target[i]
            increase_count += 1
        if (
            new[i] < old[i]
            and distance[source[i]] + new[i] < distance[target[i]]
            and distance[source[i]] + new[i] <= horizon
        ):
            decreased[decrease_count] = i
            decrease_count += 1
    if increase_count == 0 and decrease_count == 0:
        return np.empty(0, dtype=np.int32)
    size = len(parent)
    invalid = np.zeros(size if increase_count else 0, dtype=np.bool_)
    touched = [np.int32(0)]
    touched.pop()
    queue = np.empty(size if increase_count else 0, dtype=np.int32)
    cursor, end = 0, 0
    for i in range(increase_count):
        node = increased[i]
        if not invalid[node]:
            queue[end] = node
            end += 1
            invalid[node] = True
    while cursor < end:
        node = queue[cursor]
        cursor += 1
        for i in range(indptr[node], indptr[node + 1]):
            neighbor = indices[i]
            if (
                parent[neighbor] == node
                and not invalid[neighbor]
                and distance[neighbor] <= horizon
            ):
                invalid[neighbor] = True
                queue[end] = neighbor
                end += 1
            operations += 1
            if (operations & 4095) == 0:
                _check(deadline)
    for i in range(end):
        node = queue[i]
        distance[node], parent[node] = np.inf, -9999
        touched.append(np.int32(node))
    heap = [(0.0, np.int64(0), np.int64(0))]
    heap.pop()
    for i in range(end):
        node = queue[i]
        for edge in range(reverse_ptr[node], reverse_ptr[node + 1]):
            origin = reverse_indices[edge]
            if not invalid[origin] and np.isfinite(distance[origin]):
                heappush(
                    heap,
                    (
                        float(distance[origin] + reverse_weights[edge]),
                        np.int64(node),
                        np.int64(origin),
                    ),
                )
            operations += 1
            if (operations & 4095) == 0:
                _check(deadline)
    for i in range(decrease_count):
        index = decreased[i]
        origin, node = source[index], target[index]
        if np.isfinite(distance[origin]):
            heappush(
                heap,
                (
                    float(distance[origin] + new[index]),
                    np.int64(node),
                    np.int64(origin),
                ),
            )
    while heap:
        value, node, origin = heappop(heap)
        if value > horizon:
            break
        if value < distance[node]:
            distance[node], parent[node] = value, origin
            touched.append(np.int32(node))
            for edge in range(indptr[node], indptr[node + 1]):
                neighbor, weight = indices[edge], weights[edge]
                if value + weight < distance[neighbor]:
                    heappush(
                        heap,
                        (float(value + weight), np.int64(neighbor), np.int64(node)),
                    )
                operations += 1
                if (operations & 4095) == 0:
                    _check(deadline)
        operations += 1
        if (operations & 4095) == 0:
            _check(deadline)
    _check(deadline)
    return np.unique(np.asarray(touched, dtype=np.int32))


def repair(graph, reverse, distance, parent, delta, deadline=None, horizon=np.inf):
    checkpoint(deadline)
    if reverse is None:
        source, target, old, new = delta
        selected = (new > old) & (distance[target] <= horizon)
        if np.any(parent[target[selected]] == source[selected]):
            raise ValueError(
                "An affected increased parent edge requires the reverse graph"
            )
        reverse = graph
    result = _kernel(
        graph.indptr,
        graph.indices,
        graph.data,
        reverse.indptr,
        reverse.indices,
        reverse.data,
        distance,
        parent,
        *delta,
        np.inf if deadline is None else float(deadline),
        float(horizon),
    )
    checkpoint(deadline)
    return result


def warmup():
    for dtype in (np.int32, np.int64):
        pointers = np.array([0, 1, 2], dtype=dtype)
        indices = np.array([1, 0], dtype=dtype)
        weights = np.array([1.0, 1.0])
        distance = np.array([0.0, 1.0])
        parent = np.array([-9999, 0], dtype=np.int32)
        source, target = np.array([0], dtype=np.int64), np.array([1], dtype=np.int64)
        _kernel(
            pointers,
            indices,
            weights,
            pointers,
            indices,
            weights,
            distance,
            parent,
            source,
            target,
            np.array([2.0]),
            np.array([1.0]),
            np.inf,
            np.inf,
        )
