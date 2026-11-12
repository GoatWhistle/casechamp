from typing import Any
from unittest.mock import Mock

from app.adapter.road_corridor.resolver import CorridorResolver


def test_named_street_within_one_town_resolves_without_highway_reference() -> None:
    def read(query: str, parameters: Any = None) -> list[tuple[Any, ...]]:
        rows: dict[str, list[tuple[Any, ...]]] = {
            "road_reference": [],
            "corridor_places": [("town", "Town", "Region", 41.70859, 45.36844)],
            "local_road_ways": [(7, 201616290, "Lane", 0.167)],
            "corridor_edges": [(1, 2, 7), (2, 1, 7)],
            "scenario_lines": [(201616290, "Lane", 0.167, [[41.707, 45.368], [41.705, 45.369]])],
            "region_codes": [("07", "Region")],
        }
        return rows[query]

    roads = Mock(data=Mock(read=Mock(side_effect=read)))
    engine = CorridorResolver(roads)
    result = engine.resolve("Lane", "Town", "Town")
    assert result.way_ids == [201616290]
    assert result.road_ref == "Lane"
    assert result.length_km == 0.167
    assert result.regions[0].id == "07"
    assert engine.get(result.id) == result
