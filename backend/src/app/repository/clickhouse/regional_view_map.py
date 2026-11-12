from math import ceil, floor
from typing import Any

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_view_source import RegionalViewSource
from app.usecase.normative.regional_view import (
    RegionalFacilityCell,
    RegionalMapBounds,
    RegionalMapCell,
    RegionalMapView,
    RegionalRunView,
)
from app.usecase.normative.route import RouteStage


class RegionalViewMap:
    def __init__(self, reader: ClickHouseReader, source: RegionalViewSource) -> None:
        self.reader = reader
        self.source = source

    def read(
        self, view: RegionalRunView, stage: RouteStage, bounds: RegionalMapBounds, zoom: int
    ) -> RegionalMapView:
        resolution = grid_resolution(bounds, zoom)
        if self.source.normalized(view.run_id):
            origins = self.aggregate(view, stage, bounds, resolution, "rows")
            facilities = self.aggregate(view, stage, bounds, resolution, "facilities")
        else:
            record = self.source.legacy_record(view.run_id)
            origins = aggregate_legacy(
                record["baseline_rows" if stage == "baseline" else "rows"],
                view,
                bounds,
                resolution,
                True,
            )
            facilities = aggregate_legacy(record["facilities"], view, bounds, resolution, False)
        cells = [
            RegionalMapCell(
                cell_id(view.run_id, stage, resolution, row),
                row["latitude"],
                row["longitude"],
                row["n"],
                row["measured"],
                row["minimum"],
                row["maximum"],
                row["object_id"] if row["n"] == 1 else None,
                (row["west"], row["south"], row["east"], row["north"]),
            )
            for row in origins
        ]
        targets = [
            RegionalFacilityCell(
                "facility:" + cell_id(view.run_id, stage, resolution, row),
                row["latitude"],
                row["longitude"],
                row["n"],
                row["object_id"] if row["n"] == 1 else None,
                (row["west"], row["south"], row["east"], row["north"]),
            )
            for row in facilities
        ]
        return RegionalMapView(
            view.run_id,
            stage,
            view.unit,
            cells,
            sum(c.references for c in cells),
            targets,
            sum(c.facilities for c in targets),
        )

    def aggregate(
        self,
        view: RegionalRunView,
        stage: RouteStage,
        bounds: RegionalMapBounds,
        resolution: int,
        kind: str,
    ) -> list[dict[str, Any]]:
        longitude = (
            "points.longitude>={west:Float64} AND points.longitude<={east:Float64}"
            if bounds.west <= bounds.east
            else "(points.longitude>={west:Float64} OR points.longitude<={east:Float64})"
        )
        clause = f"run_id={{run:String}} AND points.latitude>={{south:Float64}} AND points.latitude<={{north:Float64}} AND {longitude}"
        cost = "distance_metres" if view.unit == "metres" else "minutes"
        if kind == "rows":
            clause += " AND stage={stage:String}"
            values = f"countIf(isNotNull(points.{cost})) AS measured,min(points.{cost}) AS minimum,max(points.{cost}) AS maximum,"
        else:
            values = ""
        return self.reader.rows(
            f"SELECT floor((points.longitude+180)/360*{{resolution:UInt32}}) AS gx,floor((points.latitude+90)/180*{{resolution:UInt32}}) AS gy,count() AS n,{values}avg(points.latitude) AS latitude,avg(points.longitude) AS longitude,any(points.id) AS object_id,min(points.longitude) AS west,min(points.latitude) AS south,max(points.longitude) AS east,max(points.latitude) AS north FROM {self.source.table}_{kind} AS points WHERE {clause} GROUP BY gx,gy ORDER BY gx,gy",
            {
                "run": view.run_id,
                "stage": stage,
                "west": bounds.west,
                "east": bounds.east,
                "south": bounds.south,
                "north": bounds.north,
                "resolution": resolution,
            },
        )


def grid_resolution(bounds: RegionalMapBounds, zoom: int) -> int:
    width = (
        bounds.east - bounds.west if bounds.west <= bounds.east else 360 - bounds.west + bounds.east
    )
    height = bounds.north - bounds.south
    resolution = 2 ** (zoom + 3)
    while (ceil(width / 360 * resolution) + 2) * (
        ceil(height / 180 * resolution) + 2
    ) > 4096 and resolution > 1:
        resolution //= 2
    return int(resolution)


def cell_id(run_id: str, stage: RouteStage, resolution: int, row: dict[str, Any]) -> str:
    return f"{run_id}:{stage}:{resolution}:{int(row['gx'])}:{int(row['gy'])}"


def aggregate_legacy(
    rows: list[dict[str, Any]],
    view: RegionalRunView,
    bounds: RegionalMapBounds,
    resolution: int,
    origins: bool,
) -> list[dict[str, Any]]:
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        latitude, longitude = row["latitude"], row["longitude"]
        if latitude is None or longitude is None or not bounds.south <= latitude <= bounds.north:
            continue
        inside = (
            bounds.west <= longitude <= bounds.east
            if bounds.west <= bounds.east
            else longitude >= bounds.west or longitude <= bounds.east
        )
        if not inside:
            continue
        key = (
            floor((longitude + 180) / 360 * resolution),
            floor((latitude + 90) / 180 * resolution),
        )
        cell = cells.setdefault(
            key,
            {
                "gx": key[0],
                "gy": key[1],
                "n": 0,
                "measured": 0,
                "minimum": None,
                "maximum": None,
                "latitude": 0.0,
                "longitude": 0.0,
                "object_id": row["id"],
                "west": longitude,
                "south": latitude,
                "east": longitude,
                "north": latitude,
            },
        )
        cell["n"] += 1
        cell["latitude"] += latitude
        cell["longitude"] += longitude
        cell["west"], cell["east"] = min(cell["west"], longitude), max(cell["east"], longitude)
        cell["south"], cell["north"] = min(cell["south"], latitude), max(cell["north"], latitude)
        cost = (
            row.get("distance_metres" if view.unit == "metres" else "minutes") if origins else None
        )
        if cost is not None:
            cell["measured"] += 1
            cell["minimum"] = cost if cell["minimum"] is None else min(cost, cell["minimum"])
            cell["maximum"] = cost if cell["maximum"] is None else max(cost, cell["maximum"])
    for cell in cells.values():
        cell["latitude"] /= cell["n"]
        cell["longitude"] /= cell["n"]
    return sorted(cells.values(), key=lambda cell: (cell["gx"], cell["gy"]))
