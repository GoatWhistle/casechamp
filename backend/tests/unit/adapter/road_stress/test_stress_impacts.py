from math import inf

import numpy as np

from app.adapter.road_graph.routing import minimum_csr
from app.adapter.road_stress.impacts import disconnected_points, point_impact
from app.usecase.road_stress import StressPoint


def test_components_exclude_self_market_and_keep_preexisting_isolation() -> None:
    points = [StressPoint(str(i), str(i), "r", 10, i, 0, 30, 50) for i in range(4)]
    markets = [("own", 0, 0, 1, "0"), ("external", 2, 0, 1, "2")]
    graph = minimum_csr(np.array([0, 1]), np.array([1, 2]), np.ones(2), 4)
    after = minimum_csr(np.array([0]), np.array([1]), np.ones(1), 4)
    assert disconnected_points(graph, points, markets).tolist() == [False, False, False, True]
    assert disconnected_points(after, points, markets).tolist() == [True, False, True, True]


def test_impacts_record_lost_and_delayed_markets_without_self_or_unreachable() -> None:
    point = StressPoint("p", "Point", "r", 10, 0, 0, 30, 50)
    impact = point_impact(point, np.array([0, 2, 3, inf]), np.array([0, 3, inf, inf]),
                          ["self", "delayed", "lost", "unreachable"], "self")
    assert impact is not None
    assert impact.worst_market == "lost"
    assert impact.lost_markets == 1
    assert impact.external_isolation is False
    assert impact.delay_minutes == 60
    assert [(m.market, m.after_hours) for m in impact.markets] == [("delayed", 3), ("lost", None)]
