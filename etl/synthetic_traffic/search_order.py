import queue
import time


class RankedResults:
    def __init__(self, tasks, output, order, projects, priorities, window):
        self.tasks, self.output = tasks, output
        self.order = [int(index) for index in order]
        self.projects, self.priorities = projects, priorities
        self.window, self.sent, self.consumed = window, 0, 0
        self.pending = {}
        self.finished = False
        self.stop_reason = "exhausted"
        self.maximum_buffer = 0
        self._dispatch()

    def _dispatch(self):
        while self.sent < len(self.order) and self.sent - self.consumed < self.window:
            index = self.order[self.sent]
            self.tasks.put((index, self.projects[index], float(self.priorities[index])))
            self.sent += 1
        if self.sent == len(self.order) and not self.finished:
            for _ in range(self.window):
                self.tasks.put(None)
            self.finished = True

    def next(self, deadline, cancelled, processes):
        if self.consumed >= len(self.order):
            return None
        expected = self.order[self.consumed]
        while True:
            if cancelled and cancelled():
                self.stop_reason = "cancelled"
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.stop_reason = "deadline"
                return None
            if expected in self.pending:
                result = self.pending.pop(expected)
                self.consumed += 1
                self._dispatch()
                return result
            try:
                result = self.output.get(timeout=min(0.05, remaining))
            except queue.Empty:
                if any(process.exitcode not in (None, 0) for process in processes):
                    self.stop_reason = "worker_failed"
                    return None
                if not any(process.is_alive() for process in processes):
                    self.stop_reason = "workers_finished"
                    return None
                continue
            index = int(result[0])
            if (
                index not in self.order[self.consumed : self.sent]
                or index in self.pending
            ):
                raise ValueError(
                    "Worker returned an unexpected or duplicate project result"
                )
            self.pending[index] = result
            self.maximum_buffer = max(self.maximum_buffer, len(self.pending))
