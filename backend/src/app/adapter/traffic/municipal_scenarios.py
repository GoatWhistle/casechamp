import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from threading import Event, Lock
from uuid import uuid4

import numpy as np
from synthetic_traffic.baseline_store import load_baseline
from synthetic_traffic.incremental import evaluate_incremental
from synthetic_traffic.projects import apply_project, corridor_parts

from app.adapter.traffic.municipal_baselines import MunicipalBaselines
from app.adapter.traffic.municipal_connectivity import MunicipalConnectivity
from app.adapter.traffic.municipal_effects import municipal_traffic_metrics
from app.adapter.traffic.municipal_selection import select_edges
from app.adapter.traffic.municipal_social import MunicipalSocialAccess
from app.adapter.traffic.visuals import metrics, roads
from app.domain.errors import DataUnavailable, DomainError, InvalidQuery
from app.usecase.municipal_scenarios import (
    MunicipalScenarioRequest,
    MunicipalTrafficBaseline,
    MunicipalTrafficEffects,
    MunicipalTrafficMetrics,
)
from app.usecase.municipal_social import MunicipalSocialEffect, restore_social
from app.usecase.traffic import (
    TrafficAlternative,
    TrafficAssignmentProgress,
    TrafficIndexChange,
    TrafficJob,
    TrafficRoad,
    TrafficScope,
    TrafficStore,
)

VERSION = "municipal_fixed_od_v1"


class MunicipalScenarioJobs:
    def __init__(self, directory: Path, store: TrafficStore, baselines: MunicipalBaselines | None = None, connectivity: MunicipalConnectivity | None = None, social: MunicipalSocialAccess | None = None) -> None:
        self.social = social
        self.connectivity = connectivity
        self.baselines = baselines
        self.directory = directory
        self.store = store
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="municipal-scenario")
        self.lock = Lock()
        self.jobs: dict[str, TrafficJob] = {}
        self.stops: dict[str, Event] = {}
        self.loaded = False

    def _load(self) -> None:
        with self.lock:
            if self.loaded:
                return
            for job in self.store.load():
                if job.version != VERSION:
                    continue
                if job.status in {"queued", "running"}:
                    job = replace(job, status="cancelled", stage="interrupted")
                    self.store.save(job)
                self.jobs[job.id] = job
                self.stops[job.id] = Event()
            self.loaded = True

    def _save(self, job: TrafficJob) -> None:
        self.store.save(job)
        with self.lock:
            self.jobs[job.id] = job

    def baseline(self, region: str, municipality: str) -> MunicipalTrafficBaseline:
        if self.baselines is None:
            raise DataUnavailable("Municipal baseline catalog is not configured")
        return self.baselines.get(region, municipality)

    def submit(self, request: MunicipalScenarioRequest) -> TrafficJob:
        self._load()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", request.baseline_id):
            raise InvalidQuery("Invalid baseline identifier")
        if request.kind not in {"capacity", "closure", "lane_closure"} or not request.way_ids:
            raise InvalidQuery("Select roads and a capacity or closure scenario")
        if request.kind == "lane_closure" and len(request.edge_indices) != 1:
            raise InvalidQuery("Choose one directed segment for lane closure")
        path = self.directory / request.baseline_id
        if not (path / "sha256").is_file():
            raise DataUnavailable("A converged published baseline is required")
        if (path / "state.json").is_file() and json.loads((path / "state.json").read_text()).get("preview"):
            raise DataUnavailable("Preliminary load is display-only; scenario routing baseline is not ready")
        if self.baselines is not None:
            published = self.baseline(request.region_id, request.municipality_id)
            if published.baseline_id != request.baseline_id:
                raise InvalidQuery("Baseline does not cover the selected municipality")
            if request.kind == "capacity" and any(
                row.way_id in request.way_ids and not row.capacity_eligible for row in published.corridors
            ):
                raise InvalidQuery("Selected road does not support the lane-addition scenario")
            if not set(request.way_ids).issubset({row.way_id for row in published.corridors}):
                raise InvalidQuery("Selected roads must intersect the municipality")
            if request.kind == "capacity" and len(set(request.way_ids)) > 1:
                baseline = self.baselines.load(request.baseline_id)
                selected = self.baselines.selected_edges(request.region_id, request.municipality_id,
                                                         baseline, request.way_ids)
                if corridor_parts(baseline.network, selected) != 1:
                    raise InvalidQuery("Selected roads must form a contiguous corridor")
        job = TrafficJob(
            id="municipal-" + uuid4().hex,
            scope=TrafficScope(region=request.region_id),
            total=4,
            provenance=json.dumps(asdict(request)),
            version=VERSION,
        )
        with self.lock:
            self.stops[job.id] = Event()
        self._save(job)
        self.pool.submit(self._run, job, request, path)
        return job

    def get(self, identifier: str) -> TrafficJob:
        self._load()
        with self.lock:
            job = self.jobs.get(identifier)
        if job is None:
            raise InvalidQuery("Unknown municipal scenario")
        return job

    def effects(self, identifier: str) -> MunicipalTrafficEffects:
        job = self.get(identifier)
        value = json.loads(job.provenance).get("municipal_effects")
        if job.status != "completed" or value is None:
            raise DataUnavailable("Municipal effects are not available for this calculation")
        return MunicipalTrafficEffects(value["municipality_id"], MunicipalTrafficMetrics(**value["before"]),
                                       MunicipalTrafficMetrics(**value["after"]), value["method"], tuple(restore_social(item) for item in value.get("social", [])))

    def cancel(self, identifier: str) -> TrafficJob:
        job = self.get(identifier)
        self.stops[identifier].set()
        if job.status == "queued":
            job = replace(job, status="cancelled", stage="cancelled")
            self._save(job)
        return job

    def _run(self, job: TrafficJob, request: MunicipalScenarioRequest, path: Path) -> None:
        def check() -> None:
            if self.stops[job.id].is_set():
                raise InterruptedError("Scenario cancelled")

        def progress(value: dict[str, object]) -> None:
            nonlocal job
            check()
            job = replace(job, assignment_progress=TrafficAssignmentProgress(
                iteration=int(str(value["iteration"])),
                relative_gap=float(str(value["relative_gap"])),
            ))
            self._save(job)

        try:
            check()
            job = replace(job, status="running", stage="loading_baseline")
            self._save(job)
            baseline = self.baselines.load(request.baseline_id) if self.baselines else load_baseline(path)
            check()
            selected_edges = (self.baselines.selected_edges(request.region_id, request.municipality_id, baseline, request.way_ids)
                              if self.baselines else [int(i) for i in np.flatnonzero(np.isin(baseline.network.way_id, request.way_ids))])
            selected_edges = select_edges(request, baseline, selected_edges)
            changed = apply_project(baseline.network, {
                "kind": request.kind, "way_ids": request.way_ids, "extra_lanes": 1, "edge_indices": selected_edges,
            })
            job = replace(job, stage="assigning_diff", completed=1, baseline=metrics(baseline.assignment))
            self._save(job)
            after = evaluate_incremental(baseline, changed, iterations=10000, check=check, progress=progress)
            if not after.converged:
                raise ValueError("Scenario assignment did not converge")
            check()
            index_changes: list[TrafficIndexChange] = []
            if self.connectivity is not None:
                job = replace(job, stage="connectivity_diff", completed=2)
                self._save(job)
                index_before, index_changes = self.connectivity.evaluate(request, baseline, changed, after.hours, check)
                job = replace(job, indices=index_before)
            social: tuple[MunicipalSocialEffect, ...] = ()
            if self.social is not None:
                job = replace(job, stage="social_access_diff", completed=3)
                self._save(job)
                social = self.social.evaluate(request, baseline, changed, after.hours, check)
            job = replace(job, stage="building_result", completed=3)
            self._save(job)
            overlay = roads(changed, baseline.assignment, after, request.way_ids,
                            len(baseline.network.source), baseline.network)
            selected_geometry = {
                ((float(baseline.network.lon[baseline.network.source[i]]), float(baseline.network.lat[baseline.network.source[i]])),
                 (float(baseline.network.lon[baseline.network.target[i]]), float(baseline.network.lat[baseline.network.target[i]])))
                for i in selected_edges
            }
            overlay = [replace(road, project=road.project and tuple(tuple(point) for point in road.coordinates) in selected_geometry)
                       for road in overlay]
            selected = np.array(selected_edges, dtype=np.int64)
            lengths = {}
            for edge in selected:
                u, v = int(baseline.network.source[edge]), int(baseline.network.target[edge])
                way = int(baseline.network.way_id[edge])
                lengths[(min(u, v), max(u, v), way)] = float(baseline.network.length_km[edge])
                if request.kind == "closure" or (request.kind == "lane_closure" and baseline.network.capacity[edge] <= 1800):
                    overlay.append(TrafficRoad(way, [
                        [float(baseline.network.lon[u]), float(baseline.network.lat[u])],
                        [float(baseline.network.lon[v]), float(baseline.network.lat[v])],
                    ], float(baseline.assignment.flow[edge]), 0,
                        float(baseline.assignment.ratio[edge]), 0, project=True, closed=True))
            lost_increased = after.unserved_vehicles_per_hour > baseline.assignment.unserved_vehicles_per_hour
            alternative = TrafficAlternative(
                id=job.id, kind=request.kind, way_ids=request.way_ids,
                length_km=sum(lengths.values()),
                vehicle_hours_saved=None if lost_increased else baseline.assignment.vehicle_hours_per_hour - after.vehicle_hours_per_hour,
                after=metrics(after), roads=overlay, indices=index_changes,
            )
            if self.baselines is not None:
                municipality = self.baselines.municipality(request.region_id, request.municipality_id)
                local = MunicipalTrafficEffects(request.municipality_id,
                    municipal_traffic_metrics(municipality, baseline.network, baseline.assignment, baseline.trips),
                    municipal_traffic_metrics(municipality, changed, after, baseline.trips), social=social)
                provenance = json.loads(job.provenance)
                provenance["municipal_effects"] = asdict(local)
                job = replace(job, provenance=json.dumps(provenance))
            check()
            self._save(replace(job, status="completed", stage="completed", completed=4,
                               alternatives=[alternative], roads=overlay))
        except InterruptedError:
            self._save(replace(job, status="cancelled", stage="cancelled"))
        except (OSError, ValueError, KeyError, DomainError, RuntimeError) as error:
            self._save(replace(job, status="failed", stage="failed", error=str(error)))

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()
        self.pool.shutdown(wait=True, cancel_futures=True)
