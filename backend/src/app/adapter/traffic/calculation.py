import json
from collections.abc import Callable
from dataclasses import asdict, replace
from functools import partial
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.assignment import assign
from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.housing import distribute
from synthetic_traffic.model import DemandParameters, Trip
from synthetic_traffic.projects import apply_project
from synthetic_traffic.source import load_network, load_places

from app.adapter.traffic.housing_clearance import clear_connections
from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.visuals import metrics, roads
from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficAlternative, TrafficIndexChange, TrafficJob, TrafficZone


class TrafficCalculation:
    def __init__(self, indices: TrafficIndices | None = None) -> None:
        self.indices = indices

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
        zones, cell = aggregate(homes, network, 2, 40)
        parameters = DemandParameters()
        trips, demand = generate(network, zones, parameters)
        if job.scope.places:
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
            if job.scope.places
            else "housing-derived local demand",
            "limits": [
                "Clipped network omits external transit and induced demand",
                "Population attraction proxy; no observed jobs or freight",
                "Static assignment; no queue length, spillback or intersection controls",
                "New links are straight endpoint sketches; terrain, water, land and costs unverified",
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

        def progress(step: int, gap: float) -> None:
            checkpoint()
            if step == 1 or step % 10 == 0:
                update(replace(job, completed=step))

        baseline = assign(network, trips, 300, 1e-3, progress)
        checkpoint()
        job = replace(
            job,
            baseline=metrics(baseline),
            roads=roads(network, baseline, baseline, [], len(network.source)),
            stage="candidates",
            completed=0,
            total=job.scope.max_projects,
        )
        update(job)
        if self.indices:
            regions = self.indices.regions(job, path)
            job = replace(
                job, stage="index", completed=0, total=len(self.indices.data.read("cities"))
            )
            update(job)
            values = self.indices.calculate(
                network,
                baseline.hours,
                regions,
                self.indices.revision(provenance),
                partial(self.indices.progress, job, update=update, checkpoint=checkpoint),
            )
            job = replace(
                job, indices=values, stage="candidates", completed=0, total=job.scope.max_projects
            )
            update(job)
        candidates = generate_candidates(network, baseline.flow, baseline.hours, baseline.ratio, 8)
        projects = self.projects(clear_connections(candidates, network, path), job.scope.max_projects)
        alternatives = []
        for index, project in enumerate(projects):
            checkpoint()
            job = replace(job, stage="comparing", completed=index, total=len(projects))
            update(job)
            changed = apply_project(network, project)
            after = assign(changed, trips, 300, 1e-3, lambda step, gap: checkpoint())
            same = all(
                (a is None) == (b is None)
                for a, b in zip(baseline.od_hours, after.od_hours, strict=True)
            )
            saving = (
                baseline.vehicle_hours_per_hour - after.vehicle_hours_per_hour
                if baseline.converged and after.converged and same
                else None
            )
            ways = project.get("way_ids", [])
            length = (
                float(project["length_km"])
                if project["kind"] == "connection"
                else float(changed.length_km[np.isin(changed.way_id, ways)].sum() / 2)
            )
            index_changes = []
            if self.indices and baseline.converged and after.converged and same:
                job = replace(
                    job,
                    stage="index_comparing",
                    completed=0,
                    total=len(self.indices.data.read("cities")),
                )
                update(job)
                values = self.indices.calculate(
                    changed,
                    after.hours,
                    regions,
                    self.indices.revision(provenance),
                    partial(self.indices.progress, job, update=update, checkpoint=checkpoint),
                )
                before_by_region = {value.region: value for value in job.indices}
                index_changes = [
                    TrafficIndexChange(
                        value.region,
                        before_by_region[value.region].value,
                        value.value,
                        value.value - before_by_region[value.region].value,
                        (value.value / before_by_region[value.region].value - 1) * 100
                        if before_by_region[value.region].value
                        else None,
                        value.population,
                    )
                    for value in values
                ]
            alternatives.append(
                TrafficAlternative(
                    str(index),
                    project["kind"],
                    ways,
                    length,
                    saving,
                    metrics(after),
                    roads(changed, baseline, after, ways, len(network.source)),
                    index_changes,
                    road_names=self.indices.names(ways) if self.indices and ways else [],
                    housing_clearance=True if project["kind"] == "connection" else None,
                )
            )
            job = replace(job, alternatives=list(alternatives), completed=index + 1)
            update(job)
        provenance["candidate_counts"] = {key: len(value) for key, value in candidates.items()}
        provenance["checked_projects"] = projects
        return replace(
            job,
            status="completed",
            stage="completed",
            completed=len(projects),
            total=len(projects),
            provenance=json.dumps(provenance, ensure_ascii=False),
        )

    @staticmethod
    def projects(candidates: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        rows = candidates["existing_corridor_projects"]
        result = []
        for kind in ["capacity", "speed", "connection"]:
            choices = candidates["connections_for_review"] if kind == "connection" else rows
            match = next((row for row in choices if row["kind"] == kind), None)
            if match is not None:
                result.append(match)
        return result[:limit]

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
