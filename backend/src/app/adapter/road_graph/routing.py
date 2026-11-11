from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import floyd_warshall

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.links import (
    apply_manual,
    apply_trunk,
    canonical_links,
    missing_removals,
)
from app.adapter.road_graph.road_profiles import requested_profiles
from app.adapter.road_graph.search_cache import SearchCache, changed_weights
from app.adapter.road_graph.shortest_paths import ShortestPaths
from app.domain.errors import InvalidQuery
from app.domain.road_analysis import SettlementAccess
from app.usecase.road_graph import RoadAddition, RoadChange
from app.usecase.transport_links import LinkChange


def minimum_csr(src: Any, dst: Any, weights: Any, count: int) -> Any:
    a = np.concatenate([src, dst]).astype(np.int64)
    b = np.concatenate([dst, src]).astype(np.int64)
    keys = a * count + b
    w = np.concatenate([weights, weights])
    order = np.argsort(keys, kind="stable")
    keys = keys[order]
    if len(keys):
        starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
        values = np.minimum.reduceat(w[order], starts).astype(np.float64)
        keys = keys[starts]
    else:
        values = np.empty(0, dtype=np.float64)
    rows = keys // count
    indptr = np.zeros(count + 1, dtype=np.int64)
    np.cumsum(np.bincount(rows, minlength=count), out=indptr[1:])
    return csr_matrix(
        (values, (keys % count).astype(np.int32), indptr.astype(np.int32)), shape=(count, count)
    )


class GraphRouting:
    def __init__(self, data: GraphData, paths: ShortestPaths | None = None) -> None:
        self.data = data
        self.paths = paths or ShortestPaths()
        self.searches = SearchCache(3)

    def calculate(
        self,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        progress: Callable[[int], None],
        addition: RoadAddition | None = None,
        links: list[LinkChange] | None = None,
        on_times: Callable[[list[str], list[str], Any], None] | None = None,
    ) -> tuple[float, int, int, int, float]:
        result, _ = self.calculate_details(
            region, scenario, changes, progress, addition, links, on_times
        )
        return result

    def networks(
        self, scenario: str, links: list[LinkChange] | None = None
    ) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
        modern = self.data.modern_model
        trunk = [] if modern and scenario.startswith("road") else self.data.read("trunk")
        manual = []
        if scenario != "road":
            manual = self.data.read(
                "manual_v2" if modern else "manual",
                {
                    "season": scenario.removeprefix("road_"),
                    "road_only": int(scenario.startswith("road_")),
                },
            )
        if not links:
            return trunk, manual
        return apply_trunk(trunk, links), apply_manual(manual, links)

    def prepare_links(self, scenario: str, links: list[LinkChange]) -> list[LinkChange]:
        if not links:
            return []
        links = canonical_links(links, [str(c[0]) for c in self.data.read("cities")])
        intercity = any(link.network == "intercity" for link in links)
        if intercity and self.data.modern_model and scenario.startswith("road"):
            raise InvalidQuery(
                "В этой модели нет межгородских ж/д и авиасвязей в дорожном сценарии"
            )
        points = {str(p[0]) for p in self.data.read("points")}
        unknown = [
            end
            for link in links
            if link.network == "local"
            for end in (link.source, link.target)
            if end != "*" and end not in points
        ]
        if unknown:
            raise InvalidQuery(
                "Местные связи задаются ID населённых пунктов из find_transport_links или "
                "find_graph_locations; не найдены: " + ", ".join(unknown[:5])
            )
        missing = missing_removals(*self.networks(scenario), links)
        if missing:
            raise InvalidQuery(
                "Удаляемых связей нет в этом сценарии: "
                + "; ".join(f"{m.mode} {m.source}–{m.target}" for m in missing)
                + ". Проверьте find_transport_links; местные связи есть только летом и зимой"
            )
        return links

    def calculate_details(
        self,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        progress: Callable[[int], None],
        addition: RoadAddition | None = None,
        links: list[LinkChange] | None = None,
        on_times: Callable[[list[str], list[str], Any], None] | None = None,
    ) -> tuple[tuple[float, int, int, int, float], tuple[SettlementAccess, ...]]:
        self.data.load()
        points = self.data.read("points")
        origins = self.data.read("origins", {"season": scenario, "region": region})
        cities = self.data.read("cities")
        modern = self.data.modern_model
        trunk, manual = self.networks(scenario, links)
        norm_rows = self.data.read("normalization")
        if not norm_rows or norm_rows[0][0] is None:
            raise ValueError("Missing normalization")
        norm = float(norm_rows[0][0])
        lookup = {p[0]: [int(p[1]), float(p[2]) / 15] for p in points}
        count = len(self.data.nodes["lat"])
        if modern:
            for city in cities:
                if city[1] >= count:
                    count = int(city[1]) + 1
                if len(city) > 4 and city[4] in lookup and city[1] >= len(self.data.nodes["lat"]):
                    lookup[city[4]] = [int(city[1]), 0.0]
        for a, b, *_ in manual:
            for point in (a, b):
                if point in lookup and lookup[point][0] < 0:
                    lookup[point] = [count, 0.0]
                    count += 1
        ms, md, mw = [], [], []
        for a, b, h, *_ in manual:
            if a in lookup and b in lookup:
                left, right = lookup[a], lookup[b]
                ms.append(left[0])
                md.append(right[0])
                mw.append(h + left[1] + right[1])
        if addition:
            ms.append(addition.source_node)
            md.append(addition.target_node)
            mw.append(addition.travel_hours)
        edges = self.data.edges
        profiles = requested_profiles(self.data, changes)
        weights, changed = changed_weights(
            edges,
            self.data.indices_for([c.way_id for c in changes]) if changes else {},
            changes,
            profiles,
        )

        def graph() -> Any:
            finite = np.isfinite(weights) & self.data.allowed_edges(scenario)
            return minimum_csr(
                np.concatenate([edges["src"][finite], ms]).astype(np.int32),
                np.concatenate([edges["dst"][finite], md]).astype(np.int32),
                np.concatenate([weights[finite], np.array(mw, dtype=np.float32)]),
                count,
            )

        progress(0)
        on = [
            (lookup[p][0], lookup[p][1], max(0, pop or 0))
            for p, pop in origins
            if p in lookup and lookup[p][0] >= 0
        ]
        nodes = np.array([p[0] for p in on], dtype=np.int32)
        snaps = np.array([p[1] for p in on])
        population = np.array([p[2] for p in on])
        total_pop = int(sum(max(0, p[1] or 0) for p in origins))
        city_nodes = np.array([c[1] for c in cities], dtype=np.int32)
        city_snaps = np.array([c[2] for c in cities], dtype=np.float64)
        road = np.empty((len(on), len(cities)), dtype=np.float32)
        city_road = np.empty((len(cities), len(cities)))
        origin_rows = {
            point: i
            for i, point in enumerate(p for p, _ in origins if p in lookup and lookup[p][0] >= 0)
        }
        targets = np.unique(
            np.concatenate(
                [np.array([v[0] for v in lookup.values() if v[0] >= 0], dtype=np.int64), city_nodes]
            )
        )
        key = None if addition else (scenario, tuple(changes), tuple(links or ()))
        every = self.searches.get(key)
        if every is None:
            every = self.paths.distances(
                graph(), city_nodes, targets, np.inf if modern else 72.0, progress
            )
            self.searches.put(key, every)
        else:
            progress(len(city_nodes))
        searched = every[:, np.searchsorted(targets, np.concatenate([nodes, city_nodes]))]
        for j in range(len(city_nodes)):
            distances = searched[j]
            road[:, j] = distances[: len(nodes)].astype(np.float32) + snaps + city_snaps[j]
            if modern and len(cities[j]) > 4 and cities[j][4] in origin_rows:
                road[origin_rows[cities[j][4]], j] = 0.0
            city_road[j] = distances[len(nodes) :] + city_snaps[j] + city_snaps
        ci = {c[0]: j for j, c in enumerate(cities)}
        for source, target, mode, hours in trunk:
            a, b = ci[source], ci[target]
            city_road[a, b] = min(
                city_road[a, b], hours + (1 if mode == "rail" else 2.5) + (84 if modern else 0)
            )
        np.fill_diagonal(city_road, 0.0)
        transfers = floyd_warshall(city_road)
        hansen = np.zeros(len(on))
        reachable = np.zeros(len(on), dtype=bool)
        travel = np.full((len(origins), len(cities)), np.inf) if on_times else None
        rows = [i for i, (p, _) in enumerate(origins) if p in origin_rows]
        for j, city in enumerate(cities):
            best = np.min(road + transfers[:, j].astype(np.float32), axis=1)
            if travel is not None:
                travel[rows, j] = best
            reachable |= np.isfinite(best)
            hansen += city[3] * np.exp(-np.log(2) / 2 * best.astype(np.float64))
        if on_times is not None:
            on_times([str(p) for p, _ in origins], [str(c[0]) for c in cities], travel)
        if total_pop <= 0:
            raise ValueError("Population must be positive")
        index = float(np.dot(hansen, population) / total_pop / norm * 100)
        connected_ids = [p for p, _ in origins if p in lookup and lookup[p][0] >= 0]
        values = {
            point_id: (float(hansen[i] / norm * 100), bool(reachable[i]))
            for i, point_id in enumerate(connected_ids)
        }
        details = tuple(
            SettlementAccess(str(p), max(0, pop or 0), *values.get(p, (0.0, False)))
            for p, pop in origins
        )
        return (index, total_pop, len(origins), changed, norm), details
