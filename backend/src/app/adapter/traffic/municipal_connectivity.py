import json
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from synthetic_traffic.incremental import IncrementalBaseline
from synthetic_traffic.model import Network

from app.adapter.road_graph.data import GraphData
from app.adapter.traffic.index_delta import IndexDelta
from app.adapter.traffic.index_values import PopulationGroup
from app.adapter.traffic.municipal_baselines import MunicipalBaselines
from app.adapter.traffic.municipal_membership import municipal_membership
from app.domain.errors import DataUnavailable
from app.usecase.municipal_indices import MunicipalIndexRepository
from app.usecase.municipal_scenarios import MunicipalScenarioRequest
from app.usecase.traffic import TrafficIndexChange, TrafficIndexValue


class MunicipalConnectivity:
    def __init__(self, graph: GraphData, baselines: MunicipalBaselines, points: MunicipalIndexRepository) -> None:
        self.graph, self.baselines, self.points = graph, baselines, points
        self.directory = baselines.directory.parent / "municipal-connectivity-baselines"

    def _spec(self, region_id: str, normalization: float | None = None) -> tuple[str, list[PopulationGroup], str, float]:
        regions = self.baselines.municipalities.atlas.regions()
        region = next(row.name for row in regions if row.id == region_id)
        boundaries = self.baselines.municipalities.run(region_id).items
        source = self.points.points(region_id, "road")
        groups = []
        membership = municipal_membership(boundaries, source.points)
        for boundary in boundaries:
            selected = membership[boundary.id]
            population = sum(max(0, row.population or 0) for row in selected)
            if population:
                groups.append(PopulationGroup(boundary.id, region, frozenset(row.point_id for row in selected), population, len(selected)))
        norm = float(self.graph.read("normalization")[0][0]) if normalization is None else normalization
        payload = {
            "graph": self.graph.revision,
            "cities": self.graph.read("cities"),
            "normalization": [(norm,)],
            "origins": self.graph.read("origins", {"season": "road", "region": region}),
            "boundaries": [asdict(row) for row in boundaries],
            "points": [asdict(row) for row in source.points],
            "method": "directed_loaded_roads_fixed_markets_population_v1",
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        return region, groups, fingerprint, norm

    def prepare(self, baseline_id: str, region_id: str, check: Callable[[], None]) -> Path:
        base = self.baselines.load(baseline_id)
        region, groups, fingerprint, norm = self._spec(region_id)
        delta = IndexDelta(self.graph, base.network, base.assignment.hours, [region], check,
                           population_groups=groups, directed=True, normalization=norm)
        path = self.directory / baseline_id / f"{region_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"fingerprint": fingerprint, "baseline_sha256": (self.baselines.directory / baseline_id / "sha256").read_text(),
                  "values": [asdict(row) for row in delta.baseline], "market_cache": str(delta.cache.directory)}
        payload = json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True)
        if path.exists():
            if json.loads(path.read_text()) != record:
                raise ValueError("Published municipal connectivity baseline is immutable")
            return path
        temporary = path.with_suffix(".pending")
        temporary.write_text(payload)
        temporary.replace(path)
        return path

    def evaluate(self, request: MunicipalScenarioRequest, base: IncrementalBaseline,
                 network: Network, hours: Any, check: Callable[[], None]) -> tuple[list[TrafficIndexValue], list[TrafficIndexChange]]:
        path = self.directory / request.baseline_id / f"{request.region_id}.json"
        if not path.exists():
            raise DataUnavailable("Municipal connectivity baseline needs offline preparation")
        record = json.loads(path.read_text())
        region, groups, fingerprint, norm = self._spec(request.region_id, float(record["values"][0]["normalization"]))
        baseline_hash = (self.baselines.directory / request.baseline_id / "sha256").read_text()
        if fingerprint != record["fingerprint"] or baseline_hash != record["baseline_sha256"]:
            raise DataUnavailable("Municipal connectivity baseline sources have changed")
        delta = IndexDelta(self.graph, base.network, base.assignment.hours, [region], check,
                           population_groups=groups, directed=True, require_cached=True, normalization=norm)
        if [asdict(row) for row in delta.baseline] != record["values"]:
            raise DataUnavailable("Municipal connectivity baseline no longer reproduces")
        check()
        after = delta.evaluate(network, hours)
        check()
        keep = {region, request.municipality_id}
        before = [row for row in delta.baseline if row.region in keep]
        values = {row.region: row for row in after}
        changes = [TrafficIndexChange(row.region, row.value, values[row.region].value,
                   values[row.region].value - row.value,
                   (values[row.region].value / row.value - 1) * 100 if row.value else None,
                   row.population) for row in before]
        return before, changes
