from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.model import Network

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.adapter.road_graph.weighted import WeightedRoads
from app.domain.errors import InvalidQuery
from app.usecase.road_graph import RoadAddition
from app.usecase.traffic import TrafficIndexValue, TrafficJob


class TrafficIndices:
    def __init__(self, data: GraphData, routing: GraphRouting) -> None:
        self.data, self.routing = data, routing

    def calculate(
        self,
        network: Network,
        hours: np.ndarray[Any, Any],
        regions: list[str],
        revision: str,
        progress: Callable[[int], None],
    ) -> list[TrafficIndexValue]:
        if revision != self.data.revision:
            raise InvalidQuery("Traffic and index graph revisions differ")
        self.data.load()
        edges = self.data.edges
        weights = edges["h"].copy()
        ids = [int(way) for way in np.unique(network.way_id) if way >= 0]
        ways = self.data.indices_for(ids)
        selected = np.flatnonzero(np.isin(edges["way_idx"], list(ways.values())))
        positions = {
            (int(edges["src"][i]), int(edges["dst"][i]), int(edges["way_idx"][i])): i
            for i in selected
        }
        additions = []
        for index, way in enumerate(network.way_id):
            source = int(network.raw_nodes[network.source[index]])
            target = int(network.raw_nodes[network.target[index]])
            if way < 0:
                additions.append(RoadAddition(source, target, float(hours[index])))
                continue
            key = (source, target, ways[int(way)])
            if key not in positions:
                raise InvalidQuery("Traffic edge identity differs from the index graph")
            weights[positions[key]] = hours[index]
        addition = min(additions, key=lambda item: item.travel_hours) if additions else None
        fingerprint = sha256(weights.tobytes()).hexdigest()
        weighted = WeightedRoads(weights, revision + fingerprint)
        results = []
        for region in regions:
            values, _ = self.routing.calculate_details(
                region, "road", [], progress, addition=addition, weighted=weighted
            )
            index_value, population, settlements, _, normalization = values
            results.append(
                TrafficIndexValue(region, index_value, population, settlements, normalization)
            )
        return results

    @staticmethod
    def revision(provenance: dict[str, Any]) -> str:
        return str(
            next(
                row["value"]
                for row in provenance["source"]["metadata"]
                if row["key"] == "graph_revision"
            )
        )

    def regions(self, job: TrafficJob, path: Path) -> list[str]:
        available = {str(row[0]) for row in self.data.read("regions")}
        counts: dict[str, float] = {}
        for row in pq.read_table(path / "places.parquet").to_pylist():
            region = str(row["region"])
            if region in available and (
                not job.scope.region or region.casefold() == job.scope.region.casefold()
            ):
                counts[region] = counts.get(region, 0) + max(0, float(row["population"] or 0))
        if not counts:
            raise InvalidQuery("Window has no regions with a calibrated index")
        return sorted(counts, key=lambda name: -counts[name])

    @staticmethod
    def progress(
        job: TrafficJob,
        completed: int,
        update: Callable[[TrafficJob], None],
        checkpoint: Callable[[], None],
    ) -> None:
        checkpoint()
        if completed == 1 or completed % 10 == 0:
            update(replace(job, completed=completed))

    def names(self, way_ids: list[int]) -> list[str]:
        values = self.data.ways(list(self.data.indices_for(way_ids).values()))
        return sorted(
            {
                str(value["name"])
                for value in values.values()
                if str(value["name"]) != str(value["way_id"])
            }
        )
