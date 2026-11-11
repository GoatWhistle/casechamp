from typing import Any

from app.adapter.road_graph.data import GraphData
from app.domain.errors import InvalidQuery


def corridor_places(data: GraphData, origin: str, destination: str) -> list[tuple[Any, ...]]:
    endpoints = []
    for query in (origin, destination):
        locations = data.read("corridor_places", {"query": query})
        if not locations:
            raise InvalidQuery("Settlement not found: " + query)
        if len(locations) != 1:
            raise InvalidQuery(
                "Settlement is ambiguous: "
                + query
                + ": "
                + ", ".join(str(p[1]) + ", " + str(p[2]) for p in locations[:8])
            )
        endpoints.append(locations[0])
    return endpoints
