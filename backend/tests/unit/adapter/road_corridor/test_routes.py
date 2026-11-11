import json
from unittest.mock import Mock

import numpy as np
from scipy.sparse import csr_matrix

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.corridor_tools import CorridorTools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors


def test_endpoint_route_crosses_different_and_missing_road_references() -> None:
    roads = Mock()
    roads.delta.base.graph = csr_matrix(
        np.array(
            [
                [0, 1, 0, 0],
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
            ],
            dtype=float,
        )
    )
    roads.data.nodes = {"lon": np.array([42.0, 42.1, 42.2, 42.3]), "lat": np.full(4, 45.0)}

    def read(query: str, params: dict[str, object] | None = None) -> list[tuple[object, ...]]:
        params = params or {}
        if query == "corridor_places":
            return (
                [("a", "Town A", "Region", 42.0, 45.0)]
                if params["query"] == "Town A"
                else [("b", "Town B", "Region", 42.3, 45.0)]
            )
        rows: dict[str, list[tuple[object, ...]]] = {
            "route_points": [("a", 0, 0.0), ("b", 3, 0.0)],
            "cities": [],
            "route_edges": [(0, 1, 1, 1.0), (1, 2, 2, 1.0), (2, 3, 3, 1.0)],
            "references_by_ids": [
                (1, 101, "First", "R-1", 1.0),
                (2, 102, "Connector", "", 1.0),
                (3, 103, "Last", "R-2", 1.0),
            ],
            "region_codes": [("region", "Region")],
            "settlement_regions": [("Region", 42.0, 45.0)],
            "scenario_lines": [
                (101, "First", 1.0, [[42.0, 45.0], [42.1, 45.0]]),
                (102, "Connector", 1.0, [[42.1, 45.0], [42.2, 45.0]]),
                (103, "Last", 1.0, [[42.2, 45.0], [42.3, 45.0]]),
            ],
        }
        return rows[query]

    roads.data.read.side_effect = read
    tools = CorridorTools(RoadCorridors(CorridorResolver(roads)))
    ctx = Mock()
    ctx.deps = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    result = json.loads(tools.resolve_road_route(ctx, "Town A", "Town B"))
    assert result["way_count"] == 3
    assert result["scope"] == "fastest_road_route_whole_osm_ways_both_directions"
    roads.submit.assert_not_called()
    calls = [call.args[0] for call in roads.data.read.call_args_list]
    assert "road_reference" not in calls
