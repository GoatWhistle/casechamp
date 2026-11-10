from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.links import intercity_links, local_links
from app.adapter.road_graph.routing import GraphRouting
from app.domain.region_names import canonical_region
from app.usecase.transport_links import PlaceName, TransportLink


class TransportCatalog:
    def __init__(self, data: GraphData, routing: GraphRouting) -> None:
        self.data = data
        self.routing = routing

    def links(
        self, network: str, scenario: str, place: str, mode: str | None
    ) -> list[TransportLink]:
        if network == "intercity":
            return intercity_links(self.routing.networks(scenario)[0], place, mode)
        rows = self.data.read("manual_named", {"season": scenario}) if scenario != "road" else []
        region = canonical_region(place, [str(r[0]) for r in self.data.read("region_list")])
        return local_links(rows, region or place, mode)

    def place_names(self, ids: list[str]) -> list[PlaceName]:
        return [
            PlaceName(str(p), str(n or p), str(r or ""))
            for p, n, r in self.data.read("place_names", {"ids": ids})
        ]
