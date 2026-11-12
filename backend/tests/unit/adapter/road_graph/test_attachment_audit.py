import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from app.adapter.road_graph.attachment_audit import (
    SettlementAttachmentConflict,
    conflicting_attachment,
)
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.usecase.road_records import RoadChange


def fixture_graph() -> tuple[dict[str, Any], dict[str, Any], int, set[int]]:
    path = Path(__file__).parents[3] / "fixtures/road_graph/izobilny-attachment.json"
    source = json.loads(path.read_text())
    ids = [row["node"] for row in source["nodes"]]
    lookup = {node: index for index, node in enumerate(ids)}
    edges = {
        "src": np.array([lookup[e["src"]] for e in source["edges"]]),
        "dst": np.array([lookup[e["dst"]] for e in source["edges"]]),
        "way_idx": np.array([e["way_idx"] for e in source["edges"]]),
    }
    nodes = {key: np.array([row[key] for row in source["nodes"]]) for key in ("lat", "lon")}
    closed = {e["way_idx"] for e in source["edges"] if e["way_id"] == 201616290}
    return edges, nodes, lookup[source["point"]["node"]], closed


def test_real_residential_stub_does_not_certify_isolation_of_izobilny() -> None:
    edges, nodes, origin, closed = fixture_graph()
    assert conflicting_attachment(edges, nodes, origin, closed)


def test_unclosed_attachment_is_valid() -> None:
    edges, nodes, origin, _ = fixture_graph()
    assert not conflicting_attachment(edges, nodes, origin, set())


def test_real_bridge_is_not_rejected_when_it_disconnects_settlement_street_network() -> None:
    src = np.array(list(range(8)) + list(range(8, 16)) + [7])
    dst = np.array(list(range(1, 8)) + [0] + list(range(9, 16)) + [8] + [8])
    edges = {"src": src, "dst": dst, "way_idx": np.arange(len(src))}
    nodes = {"lat": np.full(16, 45.36), "lon": 41.70 + np.arange(16) * 0.0001}
    assert not conflicting_attachment(edges, nodes, 0, {16})


def test_routing_rejects_false_city_loss_before_computing_index(tmp_path: Path) -> None:
    edges, nodes, origin, closed = fixture_graph()
    edges["h"] = np.ones(len(edges["src"]))

    class Snapshot:
        revision = "[]"

        def arrays(self, name: Any) -> dict[str, Any]:
            if name == "edges":
                return edges
            if name == "nodes":
                return nodes
            return {"rank": np.full(int(edges["way_idx"].max()) + 1, 5)}

        def read(self, query: Any, parameters: Any = None) -> list[tuple[Any, ...]]:
            if query == "points":
                return [("07713000001", origin, 0.0838392485)]
            if query == "way_indices":
                return [(201616290, next(iter(closed)))]
            return []

    routing = GraphRouting(GraphData(tmp_path, Snapshot()))
    with pytest.raises(SettlementAttachmentConflict, match="07713000001"):
        routing.calculate("region", "road", [RoadChange(201616290, 0)], lambda _: None)
