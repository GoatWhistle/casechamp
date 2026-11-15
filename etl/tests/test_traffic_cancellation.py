from dataclasses import replace

import pytest
from synthetic_traffic.incremental import evaluate_incremental, prepare_incremental
from synthetic_traffic.model import Trip
from test_traffic_incremental import network


def test_cancel_interrupts_loading_before_remaining_origins():
    cancelled = False
    completed = []

    def check():
        if cancelled:
            raise InterruptedError('Cancelled during flow loading')

    def progress(value):
        nonlocal cancelled
        if value['stage'] == 'loading_flows':
            completed.append(value['completed'])
            cancelled = True

    with pytest.raises(InterruptedError, match='flow loading'):
        prepare_incremental(network(), [Trip(0, 4, 2.), Trip(4, 3, 1.)],
                            check=check, progress=progress)
    assert completed == [1]


def test_cancel_interrupts_tree_repair_and_preserves_baseline():
    graph = network()
    baseline = prepare_incremental(graph, [Trip(0, 4, 2.), Trip(4, 3, 1.)])
    original = baseline.assignment.flow.copy()
    calls = 0

    def check():
        nonlocal calls
        calls += 1
        if calls == 4:
            raise InterruptedError('Cancelled during tree repair')

    with pytest.raises(InterruptedError, match='tree repair'):
        evaluate_incremental(baseline, replace(graph, free_hours=graph.free_hours * 2), check=check)
    assert calls == 4
    assert (baseline.assignment.flow == original).all()
    assert baseline.paths.check is None
