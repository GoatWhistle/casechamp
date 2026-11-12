import time
from heapq import nsmallest
from itertools import islice

from synthetic_traffic.project_dedup import independent, physical_key


def complementary_packages(network, ranked, limit, deadline=None, check=None):
    if limit < 0:
        raise ValueError("Package limit must be nonnegative")
    if not limit or len(ranked) < 2:
        return [], 0
    wanted = {
        int(way)
        for project in ranked
        for part in project.get("projects", [project])
        for way in part.get("way_ids", [])
    }
    roads = {way: set() for way in wanted}
    for a, b, way in zip(network.source, network.target, network.way_id, strict=True):
        if int(way) in roads:
            roads[int(way)].update(
                (int(network.raw_nodes[a]), int(network.raw_nodes[b]))
            )

    def footprint(project):
        nodes = set()
        for part in project.get("projects", [project]):
            nodes.update(
                value
                for way in part.get("way_ids", [])
                for value in roads.get(way, set())
            )
            if part.get("kind") in {"connection", "opening"}:
                nodes.update((part["source_node"], part["target_node"]))
        return nodes

    footprints = [footprint(project) for project in ranked]
    rejected = 0
    pairs = (
        (a, total - a)
        for total in range(1, 2 * len(ranked))
        for a in range(
            max(0, total - len(ranked) + 1), min(len(ranked), (total + 1) // 2)
        )
        if a < total - a < len(ranked)
    )

    def eligible():
        nonlocal rejected
        for a, b in islice(pairs, max(512, limit * 32)):
            if deadline is not None and time.monotonic() >= deadline:
                break
            if check:
                try:
                    check()
                except TimeoutError:
                    break
            parts = [
                *ranked[a].get("projects", [ranked[a]]),
                *ranked[b].get("projects", [ranked[b]]),
            ]
            if not independent(parts, network):
                rejected += 1
                continue
            yield (not bool(footprints[a] & footprints[b]), a + b, max(a, b), a, b)

    selected = nsmallest(limit, eligible())
    packages = []
    for _, _, _, a, b in selected:
        parts = [
            *ranked[a].get("projects", [ranked[a]]),
            *ranked[b].get("projects", [ranked[b]]),
        ]
        packages.append(
            {
                "kind": "package",
                "projects": sorted(
                    parts, key=lambda part: repr(physical_key(part, network))
                ),
            }
        )
    return packages, rejected
