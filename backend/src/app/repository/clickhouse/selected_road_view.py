from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.road_records import RoadSegment, RoadView

LIMIT = 250000
SELECTED = """((min_lon <= {selected_east:Float64} AND max_lon >= {selected_west:Float64})
OR (min_lon <= {selected_east:Float64}-360 AND max_lon >= {selected_west:Float64}-360)
OR (min_lon <= {selected_east:Float64}+360 AND max_lon >= {selected_west:Float64}+360))
AND min_lat <= {selected_north:Float64} AND max_lat >= {selected_south:Float64}"""
WHERE = (
    """min_lon <= {east:Float64} AND max_lon >= {west:Float64}
AND min_lat <= {north:Float64} AND max_lat >= {south:Float64}
AND (rank <= {level:UInt8} OR ("""
    + SELECTED
    + "))"
)


def selected_road_view(
    reader: ClickHouseReader,
    bounds: tuple[float, float, float, float],
    zoom: float,
    selected_bounds: tuple[float, float, float, float],
    version: str,
) -> RoadView:
    west, south, east, north = bounds
    sw, ss, se, sn = selected_bounds
    parameters: dict[str, float | int] = {
        "west": west,
        "south": south,
        "east": east,
        "north": north,
        "selected_west": sw,
        "selected_south": ss,
        "selected_east": se,
        "selected_north": sn,
        "level": 1 if zoom < 5 else 3 if zoom < 7 else 4 if zoom < 9 else 5,
    }
    totals = reader.rows(
        "SELECT count() AS rows, sum(edge_count) AS edges FROM plexus_graph.road_lines WHERE "
        + WHERE,
        parameters,
    )[0]
    rows = reader.rows(
        "SELECT way_id,name,highway,speed_kmh,source_node,target_node,coordinates "
        "FROM plexus_graph.road_lines WHERE " + WHERE + " ORDER BY (" + SELECTED + ") DESC,"
        "rank,way_id,source_node,target_node LIMIT " + str(LIMIT),
        parameters,
    )
    return RoadView(
        [
            RoadSegment(
                way_id=int(row["way_id"]),
                name=str(row["name"]),
                highway=str(row["highway"]),
                speed_kmh=float(row["speed_kmh"]),
                coordinates=row["coordinates"],
                source_node=int(row["source_node"]),
                target_node=int(row["target_node"]),
            )
            for row in rows
        ],
        int(totals["edges"]),
        int(totals["rows"]) > len(rows),
        version,
        "selected_region",
    )
