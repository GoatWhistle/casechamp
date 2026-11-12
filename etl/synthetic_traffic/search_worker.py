import queue
import time

from synthetic_traffic.incremental import evaluate_incremental
from synthetic_traffic.projects import apply_project


def evaluate_worker(tasks, output, network, baseline, deadline, iterations, tolerance):
    while time.monotonic() < deadline:
        try:
            task = tasks.get(timeout=min(0.05, max(0.001, deadline - time.monotonic())))
            if task is None:
                return
            index, project, priority = task
        except queue.Empty:
            continue
        try:
            changed = apply_project(network, project)
            after = evaluate_incremental(
                baseline,
                changed,
                iterations=iterations,
                tolerance=tolerance,
                deadline=deadline,
            )
            output.put((index, project, priority, after, None))
        except TimeoutError:
            return
        except ValueError as error:
            output.put((index, project, priority, None, str(error)))
