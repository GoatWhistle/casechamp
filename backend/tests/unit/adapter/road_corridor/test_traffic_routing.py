from typing import Any

import numpy as np
import pytest
from tests.unit.adapter.road_corridor.test_group_connectivity import network

from app.adapter.road_corridor.traffic import loaded_pair
from app.adapter.road_corridor.traffic_paths import TrafficPaths
from app.adapter.road_graph.routing import minimum_csr
from app.domain.traffic_diversion import TrafficAssumptions


def test_local_trip_can_bypass_bridge_approaches_after_transit_is_reassigned() -> None:
    _, roads = network()
    a = np.array([0, 1, 2, 0, 1, 2, 1, 6])
    b = np.array([1, 2, 3, 3, 4, 5, 6, 2])
    h = np.array([0.1, 0.01, 0.1, 0.4, 0.01, 0.01, 0.3, 0.3])
    baseline = minimum_csr(a, b, h, 7)
    keep = np.arange(len(a)) != 1
    changed = minimum_csr(a[keep], b[keep], h[keep], 7)

    def read(query: str, params: dict[str, Any]) -> list[tuple[Any, ...]]:
        if query == "route_edges":
            return [
                (int(x), int(y), i, float(cost))
                for i, (x, y, cost) in enumerate(zip(a, b, h, strict=True))
                if x in params["ids"] and y in params["ids"]
            ]
        if query == "references_by_ids":
            return [(i, i + 101) for i in params["ids"]]
        raise AssertionError(query)

    roads.data.read.side_effect = read
    roads.data.cost_profiles.side_effect = lambda ids: {
        way - 101: {"highway": "trunk", "lanes_total": 4 if way == 102 else 2} for way in ids
    }
    assumptions = TrafficAssumptions()
    result = loaded_pair(
        TrafficPaths(roads.data, assumptions),
        baseline,
        changed,
        (0, 0),
        (3, 0),
        {102},
        {1},
        assumptions,
    )
    assert result is not None and result.traffic is not None
    assert result.before.hours == pytest.approx(0.21 * 1.009375)
    assert result.after.hours == pytest.approx(0.4 * 1.15)
    assert result.traffic.assigned_flow_pcu_h == pytest.approx(1800)
    assert result.traffic.mean_detour_hours == pytest.approx(0.6 * 1.15)
    assert result.time_loss_pcu_hours == pytest.approx((0.69 - 0.01 * 1.009375) * 1800)
    np.testing.assert_allclose(h, [0.1, 0.01, 0.1, 0.4, 0.01, 0.01, 0.3, 0.3])
