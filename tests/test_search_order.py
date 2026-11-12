import queue
from time import monotonic
from types import SimpleNamespace

from synthetic_traffic.search_order import RankedResults


def test_skewed_worker_completion_is_consumed_in_rank_order_with_bounded_window():
    tasks, output = queue.Queue(), queue.Queue()
    projects = [{"id": value} for value in range(5)]
    ranked = RankedResults(tasks, output, [4, 1, 3, 0, 2], projects, [1, 4, 0, 3, 5], 3)
    assert [tasks.get()[0] for _ in range(3)] == [4, 1, 3]
    for index in [3, 1, 4]:
        output.put((index, projects[index], 1.0, None, None))
    process = SimpleNamespace(exitcode=None, is_alive=lambda: True)
    scored = []
    for expected in [4, 1, 3]:
        result = ranked.next(monotonic() + 1, None, [process])
        scored.append(result[0])
        assert result[0] == expected
    output.put((2, projects[2], 0.0, None, "rejected"))
    output.put((0, projects[0], 1.0, None, None))
    scored += [ranked.next(monotonic() + 1, None, [process])[0] for _ in range(2)]
    assert scored == [4, 1, 3, 0, 2]
    assert ranked.maximum_buffer <= 3


def test_rank_buffer_stops_on_cancellation_deadline_and_crash():
    for cancelled, deadline, process, reason in [
        (
            lambda: True,
            monotonic() + 1,
            SimpleNamespace(exitcode=None, is_alive=lambda: True),
            "cancelled",
        ),
        (
            None,
            monotonic() - 1,
            SimpleNamespace(exitcode=None, is_alive=lambda: True),
            "deadline",
        ),
        (
            None,
            monotonic() + 1,
            SimpleNamespace(exitcode=1, is_alive=lambda: False),
            "worker_failed",
        ),
    ]:
        ranked = RankedResults(queue.Queue(), queue.Queue(), [0], [{}], [1.0], 1)
        assert ranked.next(deadline, cancelled, [process]) is None
        assert ranked.stop_reason == reason
