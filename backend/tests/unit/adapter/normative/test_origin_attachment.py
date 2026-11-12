from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest
from tests.unit.adapter.normative.test_normative_routing import setup_routing

from app.adapter.normative.origin_attachment import GraphOriginAttachment
from app.domain.errors import DataUnavailable
from app.domain.normative.model import Origin


def test_new_object_attaches_to_road_nodes_and_long_connectors_stay_unknown() -> None:
    road, _, _ = setup_routing()
    attachment = GraphOriginAttachment(road.base)
    origin = Origin("site", "Object", None, None, None, 55.10005, 65.00005)
    result = attachment.attach([origin, replace(origin, id="far", latitude=56)], "test")
    assert result[0].node == 1
    assert result[0].snap_km is not None and 0 < result[0].snap_km < 0.01
    assert result[1].node is None and result[1].snap_km is None
    assert origin.node is None


def test_a_nearer_nonroad_node_is_not_selected() -> None:
    road, _, _ = setup_routing()
    road.base.data.nodes = {
        "lat": np.array([55.0, 55.1, 55.2, 55.10001]),
        "lon": np.array([65.0, 65.0, 65.0, 65.0]),
    }
    result = GraphOriginAttachment(road.base).attach(
        [Origin("site", "Object", None, None, None, 55.10001, 65)], "test"
    )[0]
    assert result.node == 1
    assert result.snap_km is not None and result.snap_km > 0


def test_attachment_cannot_silently_switch_graph_revisions() -> None:
    road, _, _ = setup_routing()
    attachment = GraphOriginAttachment(road.base)
    with pytest.raises(DataUnavailable, match="revision"):
        attachment.attach([], "other")
    attachment.attach([], "test")
    cast(SimpleNamespace, road.base.data).revision = "new"
    with pytest.raises(DataUnavailable, match="another"):
        attachment.attach([], "new")
