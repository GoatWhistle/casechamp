import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from synthetic_traffic.origin_snapshot import digest
from synthetic_traffic.origin_store import OriginStore


def read_initial_flows(directory: Path, source: dict, demand_sha256: str):
    record = json.loads((directory / 'checkpoint.json').read_text())
    if (record.get('stage') not in {'before_first_assignment_iteration', 'feasible_warm_start'}
            or record.get('source') != source or record.get('demand_sha256') != demand_sha256):
        raise ValueError('Initial flow checkpoint does not match the graph and demand')
    store = OriginStore(directory / 'flows', 'flows', readonly=True)
    expected = record['flows']
    if set(map(str, store)) != set(expected):
        raise ValueError('Initial flow checkpoint inventory mismatch')
    for origin in store:
        if digest(store.directory / f'{origin}.npz') != expected[str(origin)]:
            raise ValueError('Initial flow checkpoint checksum mismatch')
    return store


def feasible_initial_flow(network, trips, flows):
    demands = defaultdict(dict)
    for trip in trips:
        previous = demands[trip.origin].get(trip.destination, 0.)
        demands[trip.origin][trip.destination] = previous + trip.vehicles_per_hour
    if set(flows) != set(demands):
        raise ValueError('Initial flows must cover exactly the fixed-demand origins')
    total = np.zeros(len(network.source))
    for origin, targets in demands.items():
        values = flows[origin]
        edges = np.fromiter(values, dtype=np.int64)
        amounts = np.fromiter(values.values(), dtype=float)
        if (np.any(edges < 0) or np.any(edges >= len(total))
                or np.any(~np.isfinite(amounts)) or np.any(amounts < 0)):
            raise ValueError('Initial flows contain invalid edges or amounts')
        nodes = np.unique(np.r_[network.source[edges], network.target[edges], origin, list(targets)])
        balance = np.zeros(len(nodes))
        np.add.at(balance, np.searchsorted(nodes, network.source[edges]), amounts)
        np.add.at(balance, np.searchsorted(nodes, network.target[edges]), -amounts)
        expected = np.zeros(len(nodes))
        expected[np.searchsorted(nodes, origin)] = sum(targets.values())
        for target, amount in targets.items():
            expected[np.searchsorted(nodes, target)] -= amount
        if not np.allclose(balance, expected, rtol=1e-8, atol=1e-7):
            raise ValueError('Initial flows violate fixed-demand conservation')
        np.add.at(total, edges, amounts)
    return total
