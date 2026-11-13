from collections import defaultdict
from collections.abc import Callable
from math import log

import numpy as np
from scipy.sparse.csgraph import connected_components, dijkstra
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.model import DemandParameters, Network, Trip, Zone


def xyz(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    la, lo = np.radians(lat), np.radians(lon)
    return 6371.0088 * np.column_stack(
        (np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la))
    )


def aggregate(
    zones: list[Zone], network: Network, cell_km: float, max_zones: int
) -> tuple[list[Zone], float]:
    if not np.isfinite(cell_km) or cell_km <= 0 or max_zones < 2:
        raise ValueError("Use a positive cell size and at least two zones")
    graph, _ = route_graph(network, network.free_hours)
    _, component = connected_components(graph, directed=True, connection="strong")
    coords = xyz(np.array([z.lat for z in zones]), np.array([z.lon for z in zones]))
    if len(np.unique(component[[z.node for z in zones]])) > max_zones:
        raise ValueError(
            "Inhabited disconnected components exceed max-zones; increase the zone budget"
        )
    groups: dict[tuple[int, ...], list[Zone]] = {}
    for _ in range(60):
        groups = defaultdict(list)
        for zone, cell in zip(
            zones, np.floor(coords / cell_km).astype(np.int64), strict=True
        ):
            groups[(int(component[zone.node]), *map(int, cell))].append(zone)
        if len(groups) <= max_zones:
            break
        cell_km *= 1.5
    if len(groups) > max_zones:
        raise ValueError(
            "Too many disconnected components for the zone budget; increase max-zones"
        )
    result = []
    for index, group in enumerate(groups.values()):
        anchor = max(group, key=lambda z: (z.population, z.id))
        result.append(
            Zone(
                str(index),
                anchor.node,
                sum(z.population for z in group),
                anchor.lat,
                anchor.lon,
            )
        )
    return result, cell_km


def generate(
    network: Network, zones: list[Zone], parameters: DemandParameters,
    progress: Callable[[int, int], None] | None = None,
) -> tuple[list[Trip], dict[str, float]]:
    graph, _ = route_graph(network, network.free_hours)
    trips = []
    unavailable = 0.0
    population = np.array([z.population for z in zones])
    nodes = np.array([z.node for z in zones])
    for number, zone in enumerate(zones, 1):
        distances = dijkstra(graph, directed=True, indices=zone.node, limit=parameters.max_trip_hours)[nodes]
        if progress is not None:
            progress(number, len(zones))
        weights = population * np.exp(-log(2) * distances / parameters.half_life_hours)
        weights[nodes == zone.node] = 0
        weights[distances > parameters.max_trip_hours] = 0
        production = parameters.production(zone.population)
        if weights.sum() == 0:
            unavailable += production
            continue
        for target, demand in zip(
            nodes, production * weights / weights.sum(), strict=True
        ):
            if demand > 0:
                trips.append(Trip(zone.node, int(target), float(demand)))
    return trips, {
        "generated_vehicles_per_hour": sum(t.vehicles_per_hour for t in trips),
        "unavailable_destination_vehicles_per_hour": unavailable,
        "population": sum(z.population for z in zones),
    }
