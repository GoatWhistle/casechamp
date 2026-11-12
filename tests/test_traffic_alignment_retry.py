import time

import numpy as np
import pytest
from synthetic_traffic.alignment import route_with_retries
from synthetic_traffic.alignment_validation import AlignmentRejected, segment_details
from test_traffic_alignment import surface


def geometry(grid):
    return {
        "geometry": {
            "type": "LineString",
            "coordinates": [
                grid.coordinate((2, 2)),
                grid.coordinate((2, 3)),
                grid.coordinate((2, 4)),
            ],
        }
    }


def test_retry_penalty_is_local_and_happens_before_other_targets():
    grid = surface()
    penalties = []
    calls = []

    def find(surface, start, finish, deadline, penalty):
        penalties.append(dict(penalty))
        calls.append("route")
        return geometry(surface)

    def design(route, surface, deadline, check):
        calls.append("design")
        if len(penalties) == 1:
            raise AlignmentRejected(
                "fillet", {"reason": "terrain_grade", "cells": [(5, 5)]}
            )
        return {"accepted": True}

    raw, prepared, used, failures = route_with_retries(
        grid, [40, 50], [40.01, 50.01], None, {}, 3, find, design
    )
    assert raw is not None and prepared["accepted"]
    assert calls == ["route", "design", "route", "design"]
    assert used == 2
    assert penalties[0] == {}
    assert set(penalties[1]) == {
        (row, col) for row in range(4, 7) for col in range(4, 7)
    }
    assert all(value == 12 for value in penalties[1].values())
    assert failures == [
        {"reason": "terrain_grade", "stage": "fillet", "cells": [[5, 5]]}
    ]


def test_three_failed_attempts_do_not_relax_grade_or_obstacle_masks():
    grid = surface()
    grid.blocked[5, 5] = True
    original = grid.blocked.copy()
    attempts = []

    def find(*args):
        attempts.append(True)
        return geometry(grid)

    def reject(*args):
        raise AlignmentRejected(
            "fillet", {"reason": "blocked_or_missing_terrain", "cells": [(5, 5)]}
        )

    raw, prepared, used, failures = route_with_retries(
        grid, [40, 50], [40.01, 50.01], None, {}, 3, find, reject
    )
    assert raw is None and prepared is None
    assert len(attempts) == used == len(failures) == 3
    assert grid.max_grade == 0.08
    np.testing.assert_array_equal(grid.blocked, original)


def test_failure_contract_reports_real_profile_cells_and_deadline_still_applies():
    grid = surface()
    grid.elevation_m[4, 5] = 100
    failure = {}
    assert (
        segment_details(
            grid, grid.coordinate((4, 4)), grid.coordinate((4, 6)), failure=failure
        )
        is None
    )
    assert failure["reason"] == "terrain_grade"
    assert failure["cells"]
    with pytest.raises(TimeoutError):
        route_with_retries(
            grid,
            [40, 50],
            [40.01, 50.01],
            time.monotonic() - 1,
            {},
            3,
            lambda *args: pytest.fail("Expired retry routed"),
            lambda *args: {},
        )
