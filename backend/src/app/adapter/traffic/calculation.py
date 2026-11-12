import json
from collections.abc import Callable
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.housing import distribute
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import DemandParameters, Trip
from synthetic_traffic.source import load_network, load_places

from app.adapter.traffic.development import develop
from app.adapter.traffic.focus import resolve_focus
from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.visuals import metrics, roads
from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficJob, TrafficZone


class TrafficCalculation:
    def __init__(
        self,
        indices: TrafficIndices | None = None,
        geography: Path | None = None,
        workers: int = 32,
    ) -> None:
        self.indices, self.geography, self.workers = indices, geography, workers

    def run(
        self,
        job: TrafficJob,
        path: Path,
        update: Callable[[TrafficJob], None],
        checkpoint: Callable[[], None],
    ) -> TrafficJob:
        network = load_network(path)
        settlements, binding = load_places(path, network)
        homes, housing = distribute(path / "housing.parquet", settlements, network)
        job, focus = resolve_focus(job, path, settlements, homes)
        zones, cell = aggregate(homes, network, 2, 128)
        parameters = DemandParameters()
        trips, demand = generate(network, zones, parameters)
        if len(job.scope.places) == 2:
            trips = self.pair(job, path, network.raw_nodes)
            demand = {
                "generated_vehicles_per_hour": sum(t.vehicles_per_hour for t in trips),
                "unavailable_destination_vehicles_per_hour": 0,
                "population": sum(z.population for z in settlements),
            }
        trips = [
            Trip(t.origin, t.destination, t.vehicles_per_hour * job.scope.demand_multiplier)
            for t in trips
        ]
        if not trips:
            raise InvalidQuery(
                "No interzonal demand; use a larger area or explicit settlement pair"
            )
        canonical = json.dumps([asdict(trip) for trip in trips], sort_keys=True)
        provenance = {
            "focus": focus,
            "source": json.loads((path / "source.json").read_text()),
            "housing": housing,
            "binding": binding,
            "demand": demand,
            "parameters": asdict(parameters),
            "cell_km": cell,
            "od_pairs": len(trips),
            "demand_multiplier": job.scope.demand_multiplier,
            "generated_vehicles_per_hour": sum(t.vehicles_per_hour for t in trips),
            "demand_sha256": sha256(canonical.encode()).hexdigest(),
            "hansen": "Existing Plexus road index: 180 national markets, half-life 2h, fixed national normalization; local loaded times, outside window baseline weights; representative undirected index routing",
            "observed_traffic": False,
            "period_hours": 1,
            "scope": "one direction pair without background traffic"
            if len(job.scope.places) == 2
            else "housing-derived local demand",
            "limits": [
                "Clipped network omits external transit and induced demand",
                "Population attraction proxy; no observed jobs or freight",
                "Static assignment; no queue length, spillback or intersection controls",
                "New corridors require sourced terrain, water, building and protected-area rasters",
                "Map shows up to 800 priority directed edges plus each project",
                "Best checked alternative, not a global optimum",
            ],
        }
        job = replace(
            job,
            stage="baseline",
            zones=[TrafficZone(z.lon, z.lat, z.population) for z in zones],
            provenance=json.dumps(provenance, ensure_ascii=False),
            total=300,
        )
        update(job)

        checkpoint()
        cache = prepare_incremental(network, trips, 300, 1e-3, check=checkpoint)
        baseline = cache.assignment
        checkpoint()
        if not baseline.converged:
            raise InvalidQuery("Traffic assignment did not converge; no verified project effect")
        job = replace(
            job,
            baseline=metrics(baseline),
            roads=roads(network, baseline, baseline, [], len(network.source)),
            stage="candidates",
            completed=0,
            total=job.scope.max_projects,
        )
        update(job)
        return develop(
            job,
            path,
            network,
            trips,
            zones,
            cache,
            self.indices,
            update,
            checkpoint,
            self.geography,
            self.workers,
        )

    @staticmethod
    def pair(job: TrafficJob, path: Path, raw_nodes: np.ndarray[Any, Any]) -> list[Trip]:
        rows = pq.read_table(path / "places.parquet").to_pylist()
        nodes = []
        for name in job.scope.places:
            matches = {
                int(r["node"])
                for r in rows
                if r["node"] is not None
                and (
                    str(r["settlement"]).casefold() == name.casefold() or str(r["point_id"]) == name
                )
                and (
                    not job.scope.region
                    or str(r["region"]).casefold() == job.scope.region.casefold()
                )
            }
            if len(matches) != 1:
                raise InvalidQuery("Pair endpoint is missing or ambiguous in this window")
            node = matches.pop()
            index = int(np.searchsorted(raw_nodes, node))
            if index >= len(raw_nodes) or raw_nodes[index] != node:
                raise InvalidQuery("Pair endpoint is not bound to a road")
            nodes.append(index)
        return [Trip(nodes[0], nodes[1], job.scope.pair_flow)]
