from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event, Lock

from app.adapter.traffic.indices import TrafficIndices
from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficJob, TrafficScope, TrafficSource, TrafficStore
from app.usecase.traffic_presentation import local_times


class TrafficJobs:
    def __init__(
        self,
        source: TrafficSource,
        store: TrafficStore,
        cache: Path,
        indices: TrafficIndices | None = None,
        geography: Path | None = None,
        workers: int = 32,
    ) -> None:
        self.source, self.store, self.cache = source, store, cache
        self.indices = indices
        self.geography, self.workers = geography, workers
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
                if job.version == "municipal_fixed_od_v1":
                    continue
                if job.status in {"queued", "running"}:
                    job = replace(job, status="cancelled", stage="interrupted")
                    self.store.save(job)
                self.jobs[job.id] = job
                self.stops[job.id] = Event()
            self.loaded = True

    def submit(self, scope: TrafficScope) -> TrafficJob:
        raise InvalidQuery("Road development search has been removed; saved results are read-only")

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

    def inventory(self) -> str:
        return self.source.inventory()

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()
        self.pool.shutdown(wait=True, cancel_futures=True)
