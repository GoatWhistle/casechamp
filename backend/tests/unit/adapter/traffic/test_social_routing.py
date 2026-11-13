from dataclasses import replace

import numpy as np
import pytest
from synthetic_traffic.model import Network

from app.adapter.traffic.municipal_social import compare_source
from app.adapter.traffic.social_routing import SocialRouting
from app.domain.normative.model import AccessRow, Facility
from app.usecase.municipal_social import MunicipalSocialSource


def network() -> Network:
    return Network(
        source=np.array([0, 0, 1, 0, 2]), target=np.array([1, 1, 3, 2, 3]),
        free_hours=np.array([.1, .2, .1, .3, .3]), capacity=np.ones(5) * 100,
        length_km=np.ones(5), way_id=np.arange(5), raw_nodes=np.array([10, 20, 30, 40, 50]),
        lat=np.array([45., 45.01, 45.02, 45.03, 45.04]), lon=np.full(5, 42.),
        shared=np.full(5, -1),
    )


def origin(node: int | None = 10) -> AccessRow:
    return AccessRow('village', 'Village', None, 45., 42., None, None, None, 'unknown',
                     routing_node=node, approach_metres=0.)


def facility() -> Facility:
    return Facility('hospital', 'medical', 'Hospital', '', '', '', 45.03, 42., None, 'known')


def test_directed_parallel_edges_detour_and_loaded_weights() -> None:
    graph = network()
    router = SocialRouting(graph)
    targets = router.targets([facility()])
    assert len(targets) == 1
    baseline = router.evaluate(router.matrix(graph, graph.free_hours), [origin()], targets)
    assert baseline[0][0] == pytest.approx(12.)
    hours = np.array([np.inf, np.inf, .1, .3, .3])
    detour = router.evaluate(router.matrix(graph, hours), [origin()], targets)
    assert detour[0][0] == pytest.approx(36.)
    hours[3:] = [.4, .5]
    loaded = router.evaluate(router.matrix(graph, hours), [origin()], targets)
    assert loaded[0][0] == pytest.approx(54.)
    reverse_target = replace(facility(), latitude=45.)
    reverse = router.evaluate(router.matrix(graph, graph.free_hours), [origin(40)],
                              router.targets([reverse_target]))
    assert reverse == [(None, None, True)]


def test_disconnected_routes_are_distinct_from_unresolved_origins() -> None:
    graph = network()
    router = SocialRouting(graph)
    rows = [origin(), origin(None), origin(999), replace(origin(), approach_metres=5001)]
    result = router.evaluate(router.matrix(graph, np.full(5, np.inf)), rows,
                             router.targets([facility()]))
    assert result == [(None, None, True)] + [(None, None, False)] * 3
    assert router.targets([replace(facility(), latitude=46.)]) == []


def test_social_counts_preserve_loss_improvement_and_unknown_separately() -> None:
    rows = [replace(origin(), id=str(i)) for i in range(4)]
    source = MunicipalSocialSource('N01', 'hash', 'graph', rows, [facility()])
    before = [(20., 'hospital', True), (55., 'hospital', True),
              (80., 'hospital', True), (None, None, False)]
    after = [(None, None, True), (70., 'hospital', True),
             (50., 'hospital', True), (None, None, False)]
    result = compare_source(source, before, after, 1)
    assert (result.lost_routes, result.delayed_points, result.crossed_threshold_points) == (1, 1, 2)
    assert (result.before_within, result.after_within, result.unresolved_points) == (2, 1, 1)
    assert result.points[0].id == '0'
    assert next(point for point in result.points if point.id == '2').added_minutes == -30.
    assert result.legal_compliance_confirmed is False


def test_social_weights_reject_invalid_or_misaligned_input() -> None:
    graph = network()
    router = SocialRouting(graph)
    for hours in [np.ones(4), np.full(5, -1.), np.full(5, np.nan)]:
        with pytest.raises(ValueError):
            router.matrix(graph, hours)
