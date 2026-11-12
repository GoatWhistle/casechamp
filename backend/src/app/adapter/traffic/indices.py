from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.adapter.road_graph.data import GraphData
from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficJob


class TrafficIndices:
    def __init__(self, data: GraphData) -> None:
        self.data = data

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
                not (job.scope.region or job.scope.regions)
                or region.casefold()
                in {name.casefold() for name in (job.scope.regions or [job.scope.region])}
            ):
                counts[region] = counts.get(region, 0) + max(0, float(row["population"] or 0))
        if not counts:
            raise InvalidQuery("Window has no regions with a calibrated index")
        return sorted(counts, key=lambda name: -counts[name])

    def names(self, way_ids: list[int]) -> list[str]:
        values = self.data.ways(list(self.data.indices_for(way_ids).values()))
        return sorted(
            {
                str(value["name"])
                for value in values.values()
                if str(value["name"]) != str(value["way_id"])
            }
        )
