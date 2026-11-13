from collections import defaultdict

import numpy as np
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.model import Network
from synthetic_traffic.projects import corridor_parts

from app.usecase.municipal_scenarios import MunicipalTrafficCorridor


def municipal_corridors(network: Network, assignment: Assignment, selected: list[int],
                        names: dict[int, str]) -> list[MunicipalTrafficCorridor]:
    grouped: dict[int, list[int]] = defaultdict(list)
    for edge in selected:
        way = int(network.way_id[edge])
        if way >= 0:
            grouped[way].append(edge)
    result = []
    for way, edges in grouped.items():
        parts = corridor_parts(network, edges)
        reason = ('disconnected_segments' if parts != 1 else 'shared_lane' if
                  np.any(network.shared[edges] >= 0) else 'no_assigned_demand' if
                  not np.any(assignment.flow[edges] > 0) else None)
        lengths = {(min(int(network.source[i]), int(network.target[i])),
                    max(int(network.source[i]), int(network.target[i]))): float(network.length_km[i])
                   for i in edges}
        result.append(MunicipalTrafficCorridor(
            way, float(assignment.ratio[edges].max()),
            float(assignment.flow[edges] @ assignment.hours[edges]), sum(lengths.values()),
            names.get(way, ''), reason is None, reason, parts,
        ))
    result.sort(key=lambda row: (not row.capacity_eligible, -row.peak_ratio, -row.vehicle_hours, row.way_id))
    return result
