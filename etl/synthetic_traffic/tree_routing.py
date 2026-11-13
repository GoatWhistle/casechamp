import numpy as np
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.tree_store import Tree


def bounded_tree(graph, origin, destinations, limit):
    if np.isnan(limit) or limit <= 0:
        raise ValueError('Tree radius must be positive')
    for _ in range(5):
        distance, parent = dijkstra(graph, directed=True, indices=origin,
                                   return_predecessors=True, limit=limit)
        if all(np.isfinite(distance[node]) for node in destinations) or not np.isfinite(limit):
            return Tree(distance, parent.astype(np.int64), limit)
        limit *= 2
    distance, parent = dijkstra(graph, directed=True, indices=origin, return_predecessors=True)
    return Tree(distance, parent.astype(np.int64), np.inf)


def load_tree(tree, entries):
    pending = np.zeros(len(tree.parent))
    missing = 0.0
    times = {}
    amounts = {}
    for index, trip in entries:
        if np.isfinite(tree.distance[trip.destination]):
            times[index] = float(tree.distance[trip.destination])
            pending[trip.destination] += trip.vehicles_per_hour
        else:
            missing += trip.vehicles_per_hour
    nodes = np.flatnonzero(tree.parent >= 0)
    for node in nodes[np.argsort(-tree.distance[nodes])]:
        amount = pending[node]
        if amount:
            parent = int(tree.parent[node])
            amounts[parent, int(node)] = float(amount)
            pending[parent] += amount
    return amounts, missing, times
