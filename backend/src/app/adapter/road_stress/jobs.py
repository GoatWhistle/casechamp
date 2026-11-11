from dataclasses import replace
from hashlib import sha256
from threading import Event, Lock
from uuid import uuid4

import numpy as np

from app.adapter.log.stdlib import StdlibLogger
from app.adapter.road_graph.freight_routes import road_matrix
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.routing import minimum_csr
from app.adapter.road_graph.search_cache import SearchCache, changed_weights
from app.adapter.road_graph.selection_geometry import selection_geometry
from app.adapter.road_stress.impacts import disconnected_points, point_impact, region_impacts
from app.adapter.road_stress.routes import trace_route
from app.domain.errors import DomainError, InvalidQuery
from app.usecase.road_consequences import RegionalConsequences
from app.usecase.road_geometry import RoadGeometry
from app.usecase.road_records import RoadChange
from app.usecase.road_stress import (
    StressImpact,
    StressJob,
    StressRouteComparison,
    StressStore,
    StressSummary,
)


class StressJobs:
    def __init__(self, roads: RoadJobs, store: StressStore) -> None:
        self.roads, self.store = roads, store
        self.lock = Lock()
        self.jobs: dict[str, StressJob] = {}
        self.stops: dict[str, Event] = {}
        self.loaded = False
        self.routes = SearchCache(32)
        self.consequence_cache = SearchCache(32)

    def load(self) -> None:
        with self.lock:
            if self.loaded:
                return
            for job in self.store.load():
                if job.status in {"queued", "running"}:
                    job = replace(job, status="cancelled", stage="interrupted")
                    self.store.save(job)
                self.jobs[job.id] = job
                self.stops[job.id] = Event()
            self.loaded = True

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()

    def recent(self) -> list[StressJob]:
        self.load()
        return list(self.jobs.values())[-100:][::-1]

    def get(self, job_id: str) -> StressJob:
        self.load()
        if job_id not in self.jobs:
            raise InvalidQuery("Unknown stress test")
        return self.jobs[job_id]

    def summary(self, job_id: str, region: str = "") -> StressSummary:
        job = self.get(job_id)
        if region.isdigit():
            region = self.roads.data.region_name(region)
        if (region and region not in {r.name for r in job.regions}
                and not self.roads.data.read("region_codes", {"regions": [region]})):
            raise InvalidQuery("Unknown region; use its exact atlas name or ID")
        return StressSummary(
            job.id, job.version, job.status, job.stage, len(job.way_ids), job.parent_id, region,
            self.store.totals(job_id, region) if job.status == "completed" else None,
            job.points, job.unbound_points, job.preexisting_isolated_points,
            job.completed, job.total,
            self.consequences(job_id, region) if region and job.status == "completed" else None,
        )

    def consequences(self, job_id: str, region: str) -> RegionalConsequences:
        key = (job_id, region)
        cached = self.consequence_cache.get(key)
        if isinstance(cached, RegionalConsequences):
            return cached
        result = self.store.consequences(job_id, region)
        self.consequence_cache.put(key, result)
        return result

    def submit(self, way_ids: list[int], parent_id: str | None = None) -> StressJob:
        self.load()
        if parent_id:
            parent = self.get(parent_id)
            if parent.version != self.roads.data.version:
                raise InvalidQuery("Stress test graph version changed")
            way_ids = [*way_ids, *parent.way_ids]
        ids = sorted(set(way_ids))
        if not ids or len(ids) > 20000:
            raise InvalidQuery("Select between 1 and 20000 road ways")
        self.roads.data.indices_for(ids)
        with self.lock:
            for existing in self.jobs.values():
                if (existing.way_ids == ids and existing.version == self.roads.data.version
                        and existing.status in {"queued", "running", "completed"}):
                    return existing
            job = StressJob(uuid4().hex, self.roads.data.version, ids, parent_id)
            self.store.save(job)
            self.jobs[job.id] = job
            self.stops[job.id] = Event()
        self.roads.pool.submit(self.run, job)
        return job

    def update(self, job: StressJob) -> None:
        self.store.save(job)
        with self.lock:
            self.jobs[job.id] = job

    def cancel(self, job_id: str) -> StressJob:
        job = self.get(job_id)
        self.stops[job_id].set()
        if job.status == "queued":
            job = replace(job, status="cancelled", stage="cancelled")
            self.update(job)
        return job

    def checkpoint(self, job_id: str) -> None:
        if self.stops[job_id].is_set():
            raise InterruptedError()

    def run(self, job: StressJob) -> None:
        try:
            self.checkpoint(job.id)
            self.calculate(job)
        except InterruptedError:
            self.update(replace(self.get(job.id), status="cancelled", stage="cancelled"))
        except (DomainError, ValueError, RuntimeError, OSError) as error:
            StdlibLogger("app.road_stress").error("stress_calculation_failed", exc=error, job_id=job.id)
            self.update(replace(self.get(job.id), status="failed", error="stress_calculation_failed"))

    def calculate(self, job: StressJob) -> None:
        data = self.roads.data
        data.load()
        points = self.store.points()
        cities = data.read("cities")
        count = len(data.nodes["lat"])
        valid = [p for p in points if 0 <= p.node < count]
        markets = [c for c in cities if 0 <= int(c[1]) < count]
        targets = np.array([p.node for p in valid], dtype=np.int64)
        sources = np.array([c[1] for c in markets], dtype=np.int64)
        job = replace(job, status="running", stage="connectivity", total=len(markets),
                      points=len(points), unbound_points=len(points) - len(valid))
        self.update(job)
        keep = data.allowed_edges("road")
        baseline_graph = minimum_csr(data.edges["src"][keep], data.edges["dst"][keep],
                                     data.edges["h"][keep], count)

        changes = [RoadChange(way, 0) for way in job.way_ids]
        weights, _ = changed_weights(data.edges, data.indices_for(job.way_ids), changes)
        matrix, _, _ = road_matrix(data.edges, weights, keep, count)
        disconnected_before = disconnected_points(baseline_graph, valid, markets)
        disconnected_after = disconnected_points(matrix, valid, markets)
        job = replace(job, preexisting_isolated_points=int(disconnected_before.sum()),
                      newly_isolated_points=int((disconnected_after & ~disconnected_before).sum()))
        self.checkpoint(job.id)
        self.update(job)

        def progress(stage: str, completed: int) -> None:
            self.checkpoint(job.id)
            self.update(replace(job, stage=stage, completed=completed))

        fingerprint = sha256((job.version + "stress-road-unbounded-v1" +
                              repr([(p.id, p.node) for p in valid]) + repr(sources.tolist())).encode()).hexdigest()
        before = np.empty((len(sources), len(targets)))
        cached = set()
        for index, values in self.store.baseline(fingerprint):
            if 0 <= index < len(sources) and len(values) == len(targets):
                before[index] = values
                cached.add(index)
        missing = [i for i in range(len(sources)) if i not in cached]
        if missing:
            calculated = self.roads.paths.distances(baseline_graph, sources[missing], targets, np.inf,
                                                    lambda n: progress("baseline", len(cached) + n))
            for row, index in enumerate(missing):
                self.checkpoint(job.id)
                before[index] = calculated[row]
                self.store.save_baseline(fingerprint, index, calculated[row].tolist())
        progress("routes", 0)
        self.checkpoint(job.id)
        after = self.roads.paths.distances(matrix, sources, targets, np.inf,
                                           lambda n: progress("routes", n))
        self.update(replace(job, stage="aggregating", completed=0, total=len(valid)))
        impacts = []
        names = [str(c[0]) for c in markets]
        own = {str(c[4]): str(c[0]) for c in markets}
        for i, point in enumerate(valid):
            if i % 5000 == 0:
                self.checkpoint(job.id)
                self.update(replace(job, stage="aggregating", completed=i, total=len(valid)))
            impact = point_impact(point, before[:, i], after[:, i], names, own.get(point.id, ""))
            if impact is not None:
                impacts.append(impact)
        regions = region_impacts(impacts)
        self.store.save_impacts(job.id, impacts)
        self.checkpoint(job.id)
        self.update(replace(job, status="completed", stage="completed",
                            completed=len(markets), regions=regions))

    def impacts(self, job_id: str, region: str, offset: int, limit: int,
                bounds: tuple[float, float, float, float] | None = None) -> list[StressImpact]:
        job = self.get(job_id)
        if job.status != "completed":
            return []
        return self.store.impacts(job_id, region, offset, limit, bounds)

    def geometry(self, job_id: str) -> RoadGeometry:
        job = self.get(job_id)
        if job.version != self.roads.data.version:
            raise InvalidQuery("Stress test graph version changed")
        return selection_geometry(self.roads.data, job.way_ids)

    def route(self, job_id: str, origin: str, destination: str) -> StressRouteComparison:
        job = self.get(job_id)
        data = self.roads.data
        if job.version != data.version:
            raise InvalidQuery("Stress test graph version changed")
        key = (job.version, tuple(job.way_ids), origin, destination)
        cached = self.routes.get(key)
        if isinstance(cached, StressRouteComparison):
            return cached
        points = {p.id: p for p in self.store.points()}
        if origin not in points or destination not in points:
            raise InvalidQuery("Unknown route endpoint")
        data.load()
        e = data.edges
        count = len(data.nodes["lat"])
        allowed = data.allowed_edges("road")
        before = trace_route(*road_matrix(e, e["h"], allowed, count), data.nodes,
                             points[origin], points[destination])
        weights, _ = changed_weights(e, data.indices_for(job.way_ids),
                                     [RoadChange(way, 0) for way in job.way_ids])
        after = trace_route(*road_matrix(e, weights, allowed, count), data.nodes,
                            points[origin], points[destination])
        result = StressRouteComparison(points[origin], points[destination], before, after)
        self.routes.put(key, result)
        return result
