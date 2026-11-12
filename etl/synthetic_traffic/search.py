import multiprocessing as mp
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.incremental import IncrementalBaseline, prepare_incremental
from synthetic_traffic.model import Network, Trip, Zone
from synthetic_traffic.projects import apply_project
from synthetic_traffic.search_candidates import SearchCancelled, prepare_candidates
from synthetic_traffic.search_order import RankedResults
from synthetic_traffic.search_worker import evaluate_worker
from synthetic_traffic.surrogate import (
    ARTIFACT,
    accessibility,
    load_surrogate,
)


@dataclass
class SearchResult:
    project: dict
    network: Network
    after: Assignment
    index_delta: float
    priority: float


@dataclass
class SearchReport:
    results: list[SearchResult]
    evaluated: int
    elapsed: float
    stop_reason: str
    surrogate_version: str
    deadline: float
    verified: int = 0
    rejected: int = 0
    deduplicated: int = 0
    invalid_packages: int = 0
    distinct_projects: int = 0
    maximum_result_buffer: int = 0


def search_projects(
    network: Network,
    trips: list[Trip],
    candidates: list[dict] | dict,
    baseline_cache: IncrementalBaseline | None = None,
    limit: int = 3,
    workers: int = 32,
    seconds: float = 300,
    zones: list[Zone] | None = None,
    artifact: Path = ARTIFACT,
    iterations: int = 100,
    tolerance: float = 1e-3,
    deadline: float | None = None,
    score: Callable[[Network, Assignment], float] | None = None,
    cancelled: Callable[[], bool] | None = None,
    package_limit: int = 128,
    on_evaluated: Callable[[dict, Assignment, float, float], None] | None = None,
) -> SearchReport:
    if not 1 <= workers <= 32 or not 0 < seconds <= 300 or limit < 1:
        raise ValueError(
            "Search requires 1..32 workers, 0..300 seconds and positive result limit"
        )
    model = load_surrogate(Path(artifact))
    version = sha256(Path(artifact).read_bytes()).hexdigest()
    baseline = baseline_cache or prepare_incremental(
        network, trips, iterations=iterations, tolerance=tolerance
    )
    if not baseline.assignment.converged:
        raise ValueError("Search requires a converged baseline assignment")
    start = time.monotonic()
    deadline = min(deadline or start + seconds, start + seconds)
    if time.monotonic() >= deadline:
        return SearchReport(
            [], 0, time.monotonic() - start, "deadline", version, deadline
        )
    pool = (
        candidates
        if isinstance(candidates, list)
        else [
            p
            for key in ("existing_corridor_projects", "connections_for_review")
            for p in candidates.get(key, [])
        ]
    )
    stats = {"deduplicated": 0, "invalid_packages": 0, "distinct_projects": 0}
    if time.monotonic() >= deadline:
        return SearchReport(
            [], 0, time.monotonic() - start, "deadline", version, deadline
        )
    try:
        projects, values, stats = prepare_candidates(
            model,
            network,
            baseline.assignment,
            pool,
            package_limit,
            deadline,
            cancelled,
        )
    except (TimeoutError, SearchCancelled) as error:
        return SearchReport(
            [],
            0,
            time.monotonic() - start,
            "cancelled" if isinstance(error, SearchCancelled) else "deadline",
            version,
            deadline,
        )
    if not projects:
        return SearchReport(
            [], 0, time.monotonic() - start, "exhausted", version, deadline, **stats
        )
    order = np.argsort(-values, kind="stable")
    try:
        base_score = (
            score(network, baseline.assignment)
            if score
            else accessibility(baseline.assignment, trips, zones)
        )
    except TimeoutError:
        return SearchReport(
            [], 0, time.monotonic() - start, "deadline", version, deadline
        )
    if not np.isfinite(base_score):
        raise ValueError("Search baseline score must be finite")
    if "forkserver" in mp.get_all_start_methods():
        mp.set_forkserver_preload(["synthetic_traffic.search_worker"])
        context = mp.get_context("forkserver")
    else:
        context = mp.get_context("spawn")
    worker_count = min(workers, os.cpu_count() or 1, len(projects))
    tasks, output = context.Queue(), context.Queue()
    ordered = RankedResults(tasks, output, order, projects, values, worker_count)
    worker_args = (tasks, output, network, baseline, deadline, iterations, tolerance)
    results = []
    started = []
    evaluated = 0
    verified = 0
    rejected = 0
    reason = "exhausted"
    try:
        for _ in range(worker_count):
            if time.monotonic() >= deadline:
                reason = "deadline"
                break
            process = context.Process(target=evaluate_worker, args=worker_args)
            try:
                process.start()
            except PermissionError:
                if context.get_start_method() != "forkserver":
                    raise
                context = mp.get_context("spawn")
                process = context.Process(target=evaluate_worker, args=worker_args)
                process.start()
            started.append(process)
        while evaluated < len(projects):
            item = ordered.next(deadline, cancelled, started)
            if item is None:
                reason = ordered.stop_reason
                break
            _, project, priority, after, error = item
            evaluated += 1
            if error or after is None or not after.converged:
                rejected += 1
                continue
            changed = apply_project(network, project)
            try:
                value = (
                    score(changed, after)
                    if score
                    else accessibility(after, trips, zones)
                )
            except TimeoutError:
                if time.monotonic() < deadline:
                    rejected += 1
                    continue
                reason = "deadline"
                break
            if not np.isfinite(value):
                rejected += 1
                continue
            verified += 1
            if on_evaluated is not None:
                on_evaluated(project, after, float(value), float(base_score))
            delta = value - base_score
            if delta > 0:
                results.append(SearchResult(project, changed, after, delta, priority))
    finally:
        for process in started:
            if process.is_alive():
                process.terminate()
        for process in started:
            process.join()
        tasks.cancel_join_thread()
        output.cancel_join_thread()
        tasks.close()
        output.close()
    results.sort(key=lambda result: (-result.index_delta, -result.priority))
    return SearchReport(
        results[:limit],
        evaluated,
        time.monotonic() - start,
        reason,
        version,
        deadline,
        verified,
        rejected,
        **stats,
        maximum_result_buffer=ordered.maximum_buffer,
    )
