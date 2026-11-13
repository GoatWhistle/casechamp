from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from shapely import points
from shapely.geometry import Point, Polygon
from synthetic_traffic.source import load_network
from tests.unit.adapter.traffic.snapshot_fixture import snapshot

from app.adapter.traffic import municipal_membership as membership
from app.usecase.municipalities import Municipality


def test_edge_selection_matches_polygon_oracle_without_materializing_remote_points(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot(tmp_path)
    graph = replace(load_network(tmp_path), source=np.arange(1000), target=np.arange(1, 1001),
                    lon=np.linspace(-50., 50., 1001), lat=np.full(1001, 44.), raw_nodes=np.arange(1001),
                    free_hours=np.ones(1000), capacity=np.full(1000,1800.), length_km=np.ones(1000),
                    way_id=np.arange(1000), shared=np.full(1000,-1))
    exterior = [(-.2, 43.9), (.2, 43.9), (.2, 44.1), (-.2, 44.1), (-.2, 43.9)]
    hole = [(-.1, 43.95), (.1, 43.95), (.1, 44.05), (-.1, 44.05), (-.1, 43.95)]
    municipality = Municipality('M', 'R', 'M', 6, [[exterior, hole]], 'source', 'date', 'sha', 'polygon', 1.)
    polygon = Polygon(exterior, [hole])
    expected = [i for i in range(1000) if polygon.covers(Point((graph.lon[i] + graph.lon[i + 1]) / 2, 44.))]
    calls = []
    original = points

    def measured(coordinates: np.ndarray) -> object:
        calls.append(len(coordinates))
        return original(coordinates)

    monkeypatch.setattr(membership, 'points', measured)
    monkeypatch.setattr(membership, 'EDGE_BATCH_SIZE', 64, raising=False)
    assert membership.municipal_edge_indices(municipality, graph) == expected
    assert sum(calls) < 10
