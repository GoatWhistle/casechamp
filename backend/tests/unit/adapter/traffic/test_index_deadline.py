from typing import Any, cast

import numpy as np
import pytest

from app.adapter.traffic import index_delta
from app.adapter.traffic.index_delta import IndexDelta, RegionOrigins


@pytest.mark.parametrize("phase", ["city", "region"])
def test_values_checks_deadline_after_each_market_read(
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
) -> None:
    delta = object.__new__(IndexDelta)
    delta.cities = [("a", 0, 0.0, 1.0), ("b", 1, 0.0, 1.0), ("c", 2, 0.0, 1.0)]
    delta.trunk = []
    delta.modern = True
    delta.norm = 1.0
    delta.reference = {}
    delta.reference_transfers = None
    delta.regions = [
        RegionOrigins("R", np.array([0, 1]), np.zeros(2), np.ones(2), 2, 2, ["x", "y"])
    ]
    clock, calls = [0.0], []

    def read(cache: Any, origin: int, targets: Any) -> Any:
        calls.append(origin)
        if (phase == "city" and len(targets) == 3) or (phase == "region" and len(targets) == 2):
            clock[0] += 2
        return np.zeros(len(targets))

    monkeypatch.setattr(index_delta, "monotonic", lambda: clock[0])
    monkeypatch.setattr(delta, "distances", read)
    with pytest.raises(TimeoutError, match="Index delta deadline"):
        delta.values(cast(Any, object()), deadline=5)
    assert clock[0] == 6
    assert len(calls) == (3 if phase == "city" else 6)
