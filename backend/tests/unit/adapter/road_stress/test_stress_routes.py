import numpy as np

from app.adapter.road_graph.freight_routes import road_matrix
from app.adapter.road_stress.routes import trace_route
from app.usecase.road_stress import StressPoint


def test_parallel_road_survives_and_mileage_follows_fastest_path() -> None:
    edges = {"src": np.array([0, 0, 1]), "dst": np.array([1, 1, 2]),
             "km": np.array([10, 8, 9])}
    allowed = np.ones(3, dtype=bool)
    nodes = {"lon": np.array([30, 31, 32]), "lat": np.array([50, 50, 50])}
    a = StressPoint("a", "A", "R1", 10, 0, 0, 30, 50)
    b = StressPoint("b", "B", "R2", 20, 2, 0, 32, 50)
    before = trace_route(*road_matrix(edges, np.array([1, 2, 3]), allowed, 3), nodes, a, b)
    after = trace_route(*road_matrix(edges, np.array([np.inf, 2, 3]), allowed, 3), nodes, a, b)
    assert (before.hours, before.km) == (4, 19)
    assert (after.hours, after.km) == (5, 17)
    assert after.status == "reachable"
    closed = trace_route(*road_matrix(edges, np.array([np.inf, 2, np.inf]), allowed, 3), nodes, a, b)
    assert closed.status == "unreachable"
    assert closed.hours is None and closed.km is None and closed.coordinates == []


def test_long_path_is_not_disconnection() -> None:
    edges = {"src": np.array([0]), "dst": np.array([1]), "km": np.array([100])}
    a = StressPoint("a", "A", "R", 1, 0, 0, 0, 0)
    b = StressPoint("b", "B", "R", 1, 1, 0, 1, 1)
    route = trace_route(*road_matrix(edges, np.array([90]), np.array([True]), 2),
                        {"lon": np.array([0, 1]), "lat": np.array([0, 1])}, a, b)
    assert route.status == "reachable" and route.hours == 90
