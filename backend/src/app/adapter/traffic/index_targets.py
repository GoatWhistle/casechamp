from collections.abc import Callable
from math import asin, cos, exp, log, radians, sin, sqrt
from time import monotonic
from typing import Any

import numpy as np
from synthetic_traffic.model import Network

from app.adapter.traffic.index_delta import IndexDelta


def _expired(deadline: float, check: Callable[[], None]) -> bool:
    check()
    return monotonic() >= deadline


def _kilometers(left: tuple[float, float], right: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (*left, *right))
    value = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 12742 * asin(sqrt(min(1.0, value)))


def _rank(pairs: dict[tuple[int, int], dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        pairs.values(), key=lambda row: (-row["priority"], row["source_node"], row["target_node"])
    )[:64]


def index_route_targets(
    cache: IndexDelta,
    network: Network,
    deadline: float,
    check: Callable[[], None],
) -> list[dict[str, Any]]:
    if _expired(deadline, check):
        return []
    coordinates = {
        int(node): (float(network.lat[i]), float(network.lon[i]))
        for i, node in enumerate(network.raw_nodes)
    }
    eligible = (
        {int(n) for n in network.access_raw_nodes}
        if network.access_raw_nodes is not None
        else set(coordinates)
    )
    origins = []
    for region in cache.regions:
        for node, snap, population, point in zip(
            region.nodes, region.snaps, region.population, region.point_ids, strict=True
        ):
            if int(node) in coordinates and int(node) in eligible and population > 0:
                origins.append((float(population), int(node), float(snap), str(point)))
    origins = sorted(origins, key=lambda item: (-item[0], item[1], item[3]))[:32]
    if not origins:
        return []
    nodes = np.array([item[1] for item in origins], dtype=np.int64)
    times = np.array([cache.distances(cache.cache, int(city[1]), nodes) for city in cache.cities])
    parents: dict[int, Any] = {}
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    decay = log(2) / 2
    try:
        for origin_index, (population, source, snap, point) in enumerate(origins):
            if _expired(deadline, check):
                break
            baseline = (
                times[:, origin_index] + snap + np.array([float(city[2]) for city in cache.cities])
            )
            if cache.modern:
                for i, city in enumerate(cache.cities):
                    if len(city) > 4 and str(city[4]) == point:
                        baseline[i] = 0
            contribution = np.array([float(city[3]) for city in cache.cities]) * np.exp(
                -decay * baseline
            )
            for index in np.argsort(-contribution, kind="stable")[:8]:
                if _expired(deadline, check):
                    return _rank(pairs)
                city = cache.cities[index]
                market = int(city[1])
                if (
                    contribution[index] <= 0
                    or not np.isfinite(times[index, origin_index])
                    or baseline[index] <= 0
                ):
                    continue
                if market not in parents:
                    tree = cache.cache.trees[market]
                    parents[market] = np.load(
                        tree.directory / f"{market}-parent.npy", mmap_mode="r"
                    )
                parent = parents[market]
                target, length, segments = source, 0.0, 0
                gateway, gateway_length, gateway_segments = source, 0.0, 0
                seen = {source}
                valid = True
                while target != market:
                    if _expired(deadline, check):
                        return _rank(pairs)
                    following = int(parent[target])
                    if following < 0 or following in seen:
                        valid = False
                        break
                    if following not in coordinates:
                        break
                    length += _kilometers(coordinates[target], coordinates[following])
                    segments += 1
                    target = following
                    seen.add(target)
                    if target in eligible:
                        gateway, gateway_length, gateway_segments = target, length, segments
                    if segments >= len(coordinates) and target != market:
                        valid = False
                        break
                target, length, segments = gateway, gateway_length, gateway_segments
                if not valid or source == target or segments < 2:
                    continue
                straight = _kilometers(coordinates[source], coordinates[target])
                if straight <= 0 or length <= straight * 1.05:
                    continue
                outside = float(
                    cache.distances(cache.cache, market, np.array([target], dtype=np.int64))[0]
                )
                proposed = outside + straight / 60 + snap + float(city[2])
                priority = (
                    population
                    * float(city[3])
                    * (exp(-decay * proposed) - exp(-decay * float(baseline[index])))
                )
                if priority <= 0 or not np.isfinite(priority):
                    continue
                key = (source, target)
                candidate = {
                    "source_node": source,
                    "target_node": target,
                    "priority": priority,
                    "origin": "index_route",
                    "reason": f"Baseline market route to {city[0]} has a local detour",
                    "screening_only": True,
                    "estimated_baseline_hours": float(baseline[index]),
                    "estimated_direct_hours": proposed,
                }
                if key not in pairs or priority > pairs[key]["priority"]:
                    pairs[key] = candidate
    finally:
        for parent in parents.values():
            parent._mmap.close()
    return _rank(pairs)
