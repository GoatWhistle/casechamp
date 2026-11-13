from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any

import numpy as np
from synthetic_traffic.index_paths import DiskGraphCache
from synthetic_traffic.model import Network

from app.adapter.road_graph.data import GraphData
from app.adapter.traffic.index_edge_positions import traffic_edge_positions
from app.adapter.traffic.index_network import IndexNetwork
from app.adapter.traffic.index_values import IndexValues, PopulationGroup
from app.usecase.traffic import TrafficIndexValue


def _deadline(deadline: float | None) -> None:
    if deadline is not None and monotonic() >= deadline:
        raise TimeoutError("Index delta deadline reached")


@dataclass
class RegionOrigins:
    name: str
    nodes: Any
    snaps: Any
    population: Any
    total: int
    count: int
    point_ids: list[str]


class IndexDelta:
    def __init__(
        self,
        data: GraphData,
        network: Network,
        hours: Any,
        regions: list[str],
        checkpoint: Callable[[], None],
        population_groups: list[PopulationGroup] | None = None,
        directed: bool = False,
        require_cached: bool = False,
        normalization: float | None = None,
    ) -> None:
        self.directed = directed
        self.population_groups = population_groups or []
        data.load()
        self.modern = data.modern_model
        self.trunk = [] if self.modern else data.read("trunk")
        self.data = data
        self.cities = data.read("cities")
        self.norm = float(data.read("normalization")[0][0]) if normalization is None else normalization
        if not np.isfinite(self.norm) or self.norm <= 0:
            raise ValueError("City connectivity normalization must be finite and positive")
        points = {str(p[0]): (int(p[1]), float(p[2]) / 15) for p in data.read("points")}
        for city in self.cities:
            if (
                self.modern
                and len(city) > 4
                and str(city[4]) in points
                and int(city[1]) >= len(data.nodes["lat"])
            ):
                points[str(city[4])] = (int(city[1]), 0.0)
        self.count = max(len(data.nodes["lat"]), max(int(c[1]) + 1 for c in self.cities))
        self.regions = []
        for region in regions:
            rows = data.read("origins", {"season": "road", "region": region})
            valid = [
                (str(p), max(0, pop or 0))
                for p, pop in rows
                if str(p) in points and points[str(p)][0] >= 0
            ]
            self.regions.append(
                RegionOrigins(
                    region,
                    np.array([points[p][0] for p, _ in valid], dtype=np.int64),
                    np.array([points[p][1] for p, _ in valid]),
                    np.array([pop for _, pop in valid]),
                    int(sum(max(0, pop or 0) for _, pop in rows)),
                    len(rows),
                    [p for p, _ in valid],
                )
            )
        ids = [int(w) for w in np.unique(network.way_id) if w >= 0]
        ways = data.indices_for(ids)
        edges = data.edges
        self.positions = traffic_edge_positions(edges, network, ways, self.count)
        checkpoint()
        self.network = IndexNetwork(
            edges, data.allowed_edges("road"), self.positions, self.count, network, hours, directed=directed
        )
        self.cache = DiskGraphCache(
            self.network.base.T.tocsr() if directed else self.network.base,
            [int(c[1]) for c in self.cities],
            cache_dir=data.root / "incremental-index",
            check=checkpoint,
            require_cached=require_cached,
        )
        checkpoint()
        self.last_evaluation: dict[str, Any] = {}
        self.reference: dict[str, tuple[Any, Any]] = {}
        self.reference_transfers: Any = None
        self.baseline = self.values(self.cache)

    def evaluate(self, network: Network, hours: Any, deadline: float | None = None) -> list[TrafficIndexValue]:
        started = monotonic()
        self.last_evaluation = {
            "directed_edge_changes": 0,
            "repaired_markets": 0,
            "touched_regional_origins": 0,
            "recomputed_regional_origins": 0,
        }
        _deadline(deadline)
        changed = self.cache.fork()
        try:
            tick = monotonic()
            graph, delta = self.network.changed_with_delta(network, hours)
            if self.directed:
                graph = graph.T.tocsr()
                delta = (delta[1], delta[0], delta[2], delta[3])
            self.last_evaluation.update(
                graph_seconds=monotonic() - tick, directed_edge_changes=len(delta[0])
            )
            _deadline(deadline)
            if not len(delta[0]):
                self.last_evaluation["stop"] = "unchanged_graph"
                return self.baseline
            tick = monotonic()
            changed.update_graph(
                graph, deadline=deadline, horizon=np.inf if self.modern else 72, delta=delta
            )
            self.last_evaluation.update(
                repair_seconds=monotonic() - tick,
                repaired_markets=changed.repaired_origins,
                changed_nodes=changed.changed_nodes,
            )
            _deadline(deadline)
            if not changed.repaired_origins:
                self.last_evaluation["stop"] = "no_repaired_markets"
                return self.baseline
            return self.values(changed, deadline)
        finally:
            self.last_evaluation.update(
                considered_markets=getattr(changed, "considered_origins", 0),
                skipped_markets=getattr(changed, "skipped_origins", 0),
                repair_phases=getattr(changed, "last_update_timings", {}),
            )
            changed.close()
            self.last_evaluation["total_seconds"] = monotonic() - started

    def values(
        self, cache: DiskGraphCache, deadline: float | None = None
    ) -> list[TrafficIndexValue]:
        if not hasattr(self, "aggregation"):
            aggregation = IndexValues(self, _deadline)
            result = aggregation.prepare(cache, deadline)
            self.aggregation = aggregation
            return result
        tick = monotonic()
        try:
            return self.aggregation.evaluate(cache, deadline)
        finally:
            self.last_evaluation.update(self.aggregation.last_evaluation)
            self.last_evaluation["values_seconds"] = monotonic() - tick

    def distances(self, cache: DiskGraphCache, origin: int, targets: Any) -> Any:
        values = np.array(cache.trees[origin].distance[targets], copy=True)
        if not self.modern:
            values[values > 72] = np.inf
        return values
