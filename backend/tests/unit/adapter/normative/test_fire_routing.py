from dataclasses import replace

import numpy as np
import pytest
from tests.unit.adapter.normative.test_normative_routing import setup_routing

from app.adapter.normative.fire_routing import FireNormativeRouting
from app.domain.normative.fire import FireProfile


def test_fire_profile_uses_length_instead_of_existing_car_time() -> None:
    road, origins, facility = setup_routing()
    road.base.data.edges["km"] = np.array([1.0, 2.0, 5.0])
    profile = FireProfile(60, "Explicit control assumption")
    routing = FireNormativeRouting(road.base, profile)
    before = routing.evaluate(origins, [facility], 10, [])
    assert before[0].minutes == pytest.approx(3)
    assert routing.evaluate(origins, [facility], 10, [10])[0].minutes == pytest.approx(7)
    trace = routing.trace(origins[0], facility, [], "test")
    assert trace.minutes == pytest.approx(3)
    assert len(trace.network_coordinates) == 3
    assert trace.network_coordinates[0] == (facility.longitude, facility.latitude)
    assert trace.network_coordinates[-1] == (origins[0].longitude, origins[0].latitude)
    slower = FireNormativeRouting(road.base, FireProfile(30, profile.assumption))
    assert slower.evaluate(origins, [facility], 10, [])[0].minutes == pytest.approx(6)


def test_fire_approach_uses_the_same_explicit_speed() -> None:
    road, origins, facility = setup_routing()
    road.base.data.edges["km"] = np.array([1.0, 2.0, 5.0])
    origin = replace(origins[0], snap_km=0.5)
    routing = FireNormativeRouting(road.base, FireProfile(60, "Explicit control assumption"))
    result = routing.evaluate([origin], [facility], 10, [])[0]
    assert result.minutes == pytest.approx(3.5)
    assert routing.trace(origin, facility, [], "test").minutes == pytest.approx(result.minutes)
