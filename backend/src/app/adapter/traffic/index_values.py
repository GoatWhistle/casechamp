from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any

import numpy as np
from scipy.sparse.csgraph import floyd_warshall

from app.usecase.traffic import TrafficIndexValue


@dataclass
class RegionValues:
    raw: Any
    road: Any
    access: Any
    value: TrafficIndexValue


class IndexValues:
    def __init__(self, owner: Any, checkpoint: Callable[[float | None], None]) -> None:
        self.owner, self.check = owner, checkpoint
        self.nodes = np.array([int(c[1]) for c in owner.cities], dtype=np.int64)
        self.snaps = np.array([float(c[2]) for c in owner.cities])
        self.regions: dict[str, RegionValues] = {}
        self.city_raw: Any = None
        self.transfers: Any = None
        self.last_evaluation: dict[str, Any] = {}

    def _read(self, cache: Any, origin: int, targets: Any, deadline: float | None) -> Any:
        self.check(deadline)
        values = self.owner.distances(cache, origin, targets)
        self.check(deadline)
        return values

    def _transfers(self, raw: Any, deadline: float | None) -> Any:
        self.check(deadline)
        road = raw + self.snaps[None, :] + self.snaps[:, None]
        indices = {city[0]: i for i, city in enumerate(self.owner.cities)}
        for source, target, mode, hours in self.owner.trunk:
            a, b = indices[source], indices[target]
            road[a, b] = min(road[a, b], hours + (1 if mode == "rail" else 2.5))
        np.fill_diagonal(road, 0)
        result = floyd_warshall(road)
        self.check(deadline)
        return result

    def _access(self, road: Any, transfers: Any, selected: Any, deadline: float | None) -> Any:
        result = np.zeros(int(selected.sum()))
        for j, city in enumerate(self.owner.cities):
            self.check(deadline)
            times = np.min(road[selected] + transfers[:, j].astype(np.float32), axis=1)
            result += float(city[3]) * np.exp(-np.log(2) / 2 * times.astype(np.float64))
        self.check(deadline)
        return result

    def _road(self, raw: Any, region: Any) -> Any:
        road = np.empty(raw.shape, dtype=np.float32)
        for j, city in enumerate(self.owner.cities):
            road[:, j] = raw[:, j].astype(np.float32) + region.snaps + float(city[2])
            if self.owner.modern and len(city) > 4 and str(city[4]) in region.point_ids:
                road[region.point_ids.index(str(city[4])), j] = 0
        return road

    def prepare(self, cache: Any, deadline: float | None) -> list[TrafficIndexValue]:
        self.city_raw = np.array(
            [self._read(cache, int(node), self.nodes, deadline) for node in self.nodes]
        )
        self.transfers = self._transfers(self.city_raw, deadline)
        result = []
        for region in self.owner.regions:
            if region.total <= 0:
                raise ValueError("Population must be positive")
            raw = np.array(
                [self._read(cache, int(node), region.nodes, deadline) for node in self.nodes]
            ).T
            road = self._road(raw, region)
            access = self._access(
                road, self.transfers, np.ones(len(region.nodes), dtype=bool), deadline
            )
            value = TrafficIndexValue(
                region.name,
                float(access @ region.population / region.total / self.owner.norm * 100),
                region.total,
                region.count,
                self.owner.norm,
            )
            self.regions[region.name] = RegionValues(raw, road, access, value)
            result.append(value)
        return result

    def _matches(self, nodes: Any, targets: Any) -> tuple[Any, Any]:
        if not len(nodes) or not len(targets):
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        positions = np.searchsorted(nodes, targets)
        selected = positions < len(nodes)
        selected &= nodes[np.minimum(positions, len(nodes) - 1)] == targets
        rows = np.flatnonzero(selected)
        return rows, positions[rows]

    def evaluate(self, cache: Any, deadline: float | None) -> list[TrafficIndexValue]:
        started = monotonic()
        self.last_evaluation = {"repaired_markets": 0, "overlay_nodes": 0}
        city_raw = None
        overlays: dict[int, tuple[Any, Any]] = {}
        roads: dict[str, Any] = {}
        affected = {
            region.name: np.zeros(len(region.nodes), dtype=bool) for region in self.owner.regions
        }
        for j, market in enumerate(self.nodes):
            self.check(deadline)
            overlay = cache.trees[int(market)].overlay
            if overlay is None:
                continue
            if int(market) not in overlays:
                nodes = np.load(overlay / "nodes.npy", mmap_mode="r")
                distances = np.load(overlay / "distance.npy", mmap_mode="r")
                overlays[int(market)] = (nodes, distances)
                self.last_evaluation["repaired_markets"] += 1
                self.last_evaluation["overlay_nodes"] += len(nodes)
            nodes, distances = overlays[int(market)]
            rows, positions = self._matches(nodes, self.nodes)
            values = np.array(distances[positions], copy=True)
            if not self.owner.modern:
                values[values > 72] = np.inf
            changed = values != self.city_raw[j, rows]
            if changed.any():
                if city_raw is None:
                    city_raw = self.city_raw.copy()
                city_raw[j, rows[changed]] = values[changed]
            for region in self.owner.regions:
                self.check(deadline)
                rows, positions = self._matches(nodes, region.nodes)
                values = np.array(distances[positions], copy=True)
                if not self.owner.modern:
                    values[values > 72] = np.inf
                values = (values.astype(np.float32) + region.snaps[rows] + self.snaps[j]).astype(
                    np.float32
                )
                if self.owner.modern and len(self.owner.cities[j]) > 4:
                    point = str(self.owner.cities[j][4])
                    if point in region.point_ids:
                        values[rows == region.point_ids.index(point)] = 0
                changed = values != self.regions[region.name].road[rows, j]
                rows, values = rows[changed], values[changed]
                if len(rows):
                    if region.name not in roads:
                        roads[region.name] = self.regions[region.name].road.copy()
                    roads[region.name][rows, j] = values
                    affected[region.name][rows] = True
        self.last_evaluation["overlay_seconds"] = monotonic() - started
        self.last_evaluation["touched_regional_origins"] = sum(
            int(mask.sum()) for mask in affected.values()
        )
        tick = monotonic()
        transfers = self.transfers if city_raw is None else self._transfers(city_raw, deadline)
        same = np.array_equal(transfers, self.transfers)
        self.last_evaluation.update(transfers_changed=not same, transfer_seconds=monotonic() - tick)
        tick = monotonic()
        result, recomputed = [], 0
        for region in self.owner.regions:
            self.check(deadline)
            reference = self.regions[region.name]
            selected = affected[region.name] if same else np.ones(len(region.nodes), dtype=bool)
            if not selected.any():
                result.append(reference.value)
                continue
            road = roads.get(region.name, reference.road)
            access = reference.access.copy()
            access[selected] = self._access(road, transfers, selected, deadline)
            recomputed += int(selected.sum())
            result.append(
                TrafficIndexValue(
                    region.name,
                    float(access @ region.population / region.total / self.owner.norm * 100),
                    region.total,
                    region.count,
                    self.owner.norm,
                )
            )
        self.check(deadline)
        self.last_evaluation.update(
            recomputed_regional_origins=recomputed,
            aggregate_seconds=monotonic() - tick,
            values_seconds=monotonic() - started,
        )
        return result
