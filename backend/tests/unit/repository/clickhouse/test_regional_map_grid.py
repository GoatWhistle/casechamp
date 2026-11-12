from typing import cast
from unittest.mock import Mock

from app.repository.clickhouse.regional_view_map import aggregate_legacy, grid_resolution
from app.usecase.normative.regional_view import RegionalMapBounds, RegionalRunView


def test_display_aggregation_keeps_every_reference_and_unknown_measurement() -> None:
    bounds = RegionalMapBounds(-180, -90, 180, 90)
    view = Mock(spec=RegionalRunView)
    view.unit = "metres"
    rows = [
        {
            "id": f"p{x}:{y}",
            "latitude": -80 + y * 1.6,
            "longitude": -179 + x * 3.58,
            "distance_metres": None if (x + y) % 2 else float(x + y),
        }
        for x in range(100)
        for y in range(100)
    ]
    cells = aggregate_legacy(
        rows, cast(RegionalRunView, view), bounds, grid_resolution(bounds, 20), True
    )
    assert len(cells) <= 4096
    assert sum(cell["n"] for cell in cells) == 10000
    assert sum(cell["measured"] for cell in cells) == 5000
    assert all(cell["minimum"] is None or cell["minimum"] <= cell["maximum"] for cell in cells)
