from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.bridge_tools import BridgeTools
from app.adapter.chat.corridor_tools import CorridorTools
from app.adapter.chat.road_tools import RoadTools
from app.adapter.chat.transport_requests import (
    BridgeSearch,
    GraphPlaceSearch,
    RoadSearch,
    ServiceSearch,
    TransportSearch,
)
from app.adapter.chat.transport_tools import TransportTools
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph


class NetworkSearch:
    def __init__(self, roads: RoadGraph | None, corridors: RoadCorridors | None) -> None:
        self.roads = roads
        self.corridors = corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Find transport assets using one typed request. road: endpoints, optional "
            "road_name restricts to that highway; without a name search the complete road graph. "
            "bridges: near/name/radius. services: rail/air/seasonal links in the calculation "
            "snapshot. graph_places: real node IDs for a new connection. road_viewport: sampled "
            "OSM ways in bounds. Returns real selections/IDs, never modifies the graph.",
        )(self.find_transport)

    def find_transport(self, ctx: RunContext[ChatRun], request: TransportSearch) -> str:
        if isinstance(request, (RoadSearch, BridgeSearch)):
            if self.corridors is None:
                raise ModelRetry("Road selection is unavailable; query capabilities")
            if isinstance(request, BridgeSearch):
                return BridgeTools(self.corridors).find_road_bridges(
                    ctx, request.near, request.radius_km, request.name
                )
            corridor_tools = CorridorTools(self.corridors)
            if request.road_name:
                return corridor_tools.resolve_road_corridor(
                    ctx, request.road_name, request.origin, request.destination
                )
            return corridor_tools.resolve_road_route(ctx, request.origin, request.destination)
        if self.roads is None:
            raise ModelRetry("Calculation graph is unavailable; query capabilities")
        if isinstance(request, ServiceSearch):
            return TransportTools(self.roads).find_transport_links(
                ctx, request.network, request.place, request.scenario, request.mode
            )
        road_tools = RoadTools(self.roads)
        if isinstance(request, GraphPlaceSearch):
            return road_tools.find_graph_locations(ctx, request.query, request.region_id)
        return road_tools.read_road_graph(
            ctx, request.west, request.south, request.east, request.north, request.zoom
        )
