from typing import cast

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.selected_road_view import selected_road_view


class Reader:
    def rows(self, sql: str, parameters: dict[str, float | int]) -> list[dict[str, object]]:
        assert parameters["level"] == 1
        assert parameters["selected_west"] == 40
        assert "OR (min_lon" in sql
        assert "selected_east:Float64}-360" in sql
        if "count()" in sql:
            return [{"rows": 300000, "edges": 350000}]
        assert "LIMIT 250000" in sql
        assert "DESC,rank,way_id,source_node,target_node" in sql
        return [
            {
                "way_id": 1,
                "name": "Local",
                "highway": "residential",
                "speed_kmh": 30,
                "source_node": 1,
                "target_node": 2,
                "coordinates": [[40, 44], [41, 45]],
            }
        ]


def test_selected_bbox_keeps_local_roads_at_low_zoom_with_honest_limit() -> None:
    view = selected_road_view(
        cast(ClickHouseReader, Reader()), (35, 40, 45, 50), 4, (40, 44, 41, 45), "version"
    )
    assert view.segments[0].highway == "residential"
    assert view.truncated
    assert view.matched == 350000
    assert view.detail == "selected_region"
