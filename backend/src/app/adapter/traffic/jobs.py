from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from math import isfinite
from pathlib import Path
from threading import Event, Lock
from uuid import uuid4

from app.adapter.log.stdlib import StdlibLogger
from app.adapter.traffic.calculation import TrafficCalculation
from app.adapter.traffic.indices import TrafficIndices
from app.domain.errors import DomainError, InvalidQuery
from app.usecase.traffic import TrafficJob, TrafficScope, TrafficSource, TrafficStore
from app.usecase.traffic_presentation import local_times


class TrafficJobs:
    def __init__(
        self,
        source: TrafficSource,
        store: TrafficStore,
        cache: Path,
        indices: TrafficIndices | None = None,
    ) -> None:
        self.source, self.store, self.cache = source, store, cache
        self.indices = indices
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="traffic")
        self.lock = Lock()
        self.jobs: dict[str, TrafficJob] = {}
        self.stops: dict[str, Event] = {}
        self.loaded = False

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

    def submit(self, scope: TrafficScope) -> TrafficJob:
        if (
            len(scope.places) not in {0, 2}
            or not 1 <= scope.max_projects <= 3
            or not isfinite(scope.demand_multiplier)
            or not 0.1 <= scope.demand_multiplier <= 3
            or not isfinite(scope.pair_flow)
            or not 0 < scope.pair_flow <= 10000
        ):
            raise InvalidQuery(
                "Use two places, 1-3 projects, demand x0.1-3 and pair flow up to 10000"
            )
        self.load()
        bounds = self.source.resolve(scope)
        with self.lock:
            active = [j for j in self.jobs.values() if j.status in {"queued", "running"}]
            if len(active) >= 3:
                raise InvalidQuery("Traffic queue is full; wait or cancel a saved job")
            job = TrafficJob("traffic-" + uuid4().hex, scope, bounds=bounds)
            self.store.save(job)
            self.jobs[job.id] = job
            self.stops[job.id] = Event()
        self.pool.submit(self.run, job)
        return job

    def get(self, job_id: str) -> TrafficJob:
        self.load()
        with self.lock:
            if job_id not in self.jobs:
                raise InvalidQuery("Unknown traffic calculation")
            return local_times(self.jobs[job_id])

    def recent(self) -> list[TrafficJob]:
        self.load()
        with self.lock:
            return list(self.jobs.values())[-100:][::-1]

    def update(self, job: TrafficJob) -> None:
        self.store.save(job)
        with self.lock:
            self.jobs[job.id] = job

    def cancel(self, job_id: str) -> TrafficJob:
        job = self.get(job_id)
        self.stops[job_id].set()
        if job.status == "queued":
            job = replace(job, status="cancelled", stage="cancelled")
            self.update(job)
        return job

    def checkpoint(self, job_id: str) -> None:
        if self.stops[job_id].is_set():
            raise InterruptedError()

    def run(self, job: TrafficJob) -> None:
        try:
            self.checkpoint(job.id)
            job = replace(job, status="running", stage="loading")
            self.update(job)
            path = self.cache / "traffic" / job.id
            self.source.export(job.bounds, path)
            self.checkpoint(job.id)
            result = TrafficCalculation(self.indices).run(
                job, path, self.update, lambda: self.checkpoint(job.id)
            )
            self.checkpoint(job.id)
            self.update(result)
        except InterruptedError:
            self.update(replace(self.get(job.id), status="cancelled", stage="cancelled"))
        except (
            DomainError,
            ValueError,
            RuntimeError,
            OSError,
            TypeError,
            IndexError,
            KeyError,
        ) as error:
            StdlibLogger("app.traffic").error(
                "traffic_calculation_failed", exc=error, job_id=job.id
            )
            code = (
                "traffic_scope_too_large"
                if "exceeds" in str(error)
                else "traffic_calculation_failed"
            )
            self.update(replace(self.get(job.id), status="failed", stage="failed", error=code))

    def inventory(self) -> str:
        return self.source.inventory()

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()
        self.pool.shutdown(wait=True, cancel_futures=True)
        if self.indices:
            self.indices.routing.paths.close()
