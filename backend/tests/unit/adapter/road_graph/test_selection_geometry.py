from unittest.mock import Mock

import pytest

from app.adapter.road_graph.selection_geometry import selection_geometry
from app.domain.errors import DataUnavailable


def test_whole_way_geometry_keeps_all_segments_and_counts_length_once() -> None:
    data = Mock()
    data.read.return_value = [
        (7, "R-1", 4, [[40.0, 44.0], [41.0, 45.0]]),
        (7, "R-1", 4, [[41.0, 45.0], [42.0, 46.0]]),
        (8, "R-1", 3, [[42.0, 46.0], [43.0, 47.0]]),
    ]
    result = selection_geometry(data, [7, 8])
    assert result.names == ["R-1"]
    assert result.length_km == 7
    assert len(result.lines) == 3


def test_partial_geometry_cannot_be_presented_as_the_whole_scenario() -> None:
    data = Mock()
    data.read.return_value = [(7, "R-1", 4, [[40.0, 44.0], [41.0, 45.0]])]
    with pytest.raises(DataUnavailable, match="Geometry is missing"):
        selection_geometry(data, [7, 8])
