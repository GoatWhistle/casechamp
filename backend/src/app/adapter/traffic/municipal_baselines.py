import json
from pathlib import Path
from threading import Lock

import numpy as np
from synthetic_traffic.baseline_store import load_baseline
from synthetic_traffic.incremental import IncrementalBaseline

from app.adapter.road_graph.data import GraphData
from app.adapter.traffic.municipal_corridors import municipal_corridors
from app.adapter.traffic.municipal_membership import municipal_edge_indices
from app.adapter.traffic.municipal_road_view import baseline_roads
from app.adapter.traffic.visuals import metrics
from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.municipal_scenarios import MunicipalTrafficBaseline
from app.usecase.municipalities import Municipality, MunicipalityQueries
from app.usecase.traffic import TrafficJob, TrafficScope


class MunicipalBaselines:
    def __init__(self, directory: Path, municipalities: MunicipalityQueries, graph: GraphData | None = None) -> None:
        self.graph = graph
        self._cache: tuple[str, IncrementalBaseline] | None = None
        self._lock = Lock()
        self.directory = directory
        self.municipalities = municipalities

    def load(self, identifier: str) -> IncrementalBaseline:
        with self._lock:
            if self._cache is None or self._cache[0] != identifier:
                self._cache = (identifier, load_baseline(self.directory / identifier))
            return self._cache[1]

    def municipality(self, region: str, identifier: str) -> Municipality:
        result = next((item for item in self.municipalities.run(region).items if item.id == identifier), None)
        if result is None:
            raise InvalidQuery("Municipality is not available in this region")
        return result

    def get(self, region: str, identifier: str) -> MunicipalTrafficBaseline:
        municipality = self.municipality(region, identifier)
        vertices = [point for polygon in municipality.coordinates for ring in polygon for point in ring]
        for path in sorted(self.directory.glob("*/state.json"), reverse=True):
            if not (path.parent / "sha256").is_file():
                continue
            record = json.loads(path.read_text())
            region_ids = record.get("metadata", {}).get("region_ids")
            if region_ids and region not in region_ids:
                continue
            bounds = record.get("metadata", {}).get("source", {}).get("bounds")
            if not vertices or (bounds and not all(bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3] for x, y in vertices)):
                continue
            baseline = self.load(path.parent.name)
            graph, assignment = baseline.network, baseline.assignment
            selected = municipal_edge_indices(municipality, graph)
            if not selected:
                continue
            names: dict[int, str] = {}
            if self.graph is not None:
                indices = self.graph.indices_for([int(value) for value in np.unique(graph.way_id[selected])])
                names = {int(row["way_id"]): str(row["name"]) for row in self.graph.ways(list(indices.values())).values()}
            corridors = municipal_corridors(graph, assignment, selected, names)
            roads = baseline_roads(baseline, selected)
            view = TrafficJob(id="municipal-baseline-" + path.parent.name + "-" + identifier, scope=TrafficScope(region=region),
                              status="completed", stage="completed", completed=1,
                              bounds=[min(x for x, _ in vertices), min(y for _, y in vertices),
                                      max(x for x, _ in vertices), max(y for _, y in vertices)],
                              baseline=metrics(assignment), roads=roads, version="municipal_fixed_od_v1")
            return MunicipalTrafficBaseline(path.parent.name, identifier, corridors, roads,
                                            assignment.relative_gap, bounds, (path.parent / "sha256").read_text(), view)
        raise DataUnavailable("No published traffic baseline covers this municipality")

    def selected_edges(self, region: str, municipality_id: str, baseline: IncrementalBaseline, ways: list[int]) -> list[int]:
        municipality = self.municipality(region, municipality_id)
        graph = baseline.network
        selected = municipal_edge_indices(municipality, graph)
        return [i for i in selected if int(graph.way_id[i]) in ways]
