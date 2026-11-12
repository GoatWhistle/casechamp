from app.domain.normative.model import AccessRow
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative_schema import SCHEMAS
from app.repository.clickhouse.regional_view_map import RegionalViewMap
from app.repository.clickhouse.regional_view_source import RegionalViewSource, access_row, facility
from app.usecase.normative.regional_view import (
    RegionalFacilityPage,
    RegionalMapBounds,
    RegionalMapView,
    RegionalPointDetail,
    RegionalRowPage,
    RegionalRunView,
    RowSort,
)
from app.usecase.normative.route import RouteStage


class ClickHouseRegionalViewRepository:
    def __init__(
        self, reader: ClickHouseReader, table: str = "plexus_normative.regional_measurements"
    ) -> None:
        self.reader = reader
        self.table = table
        self.source = RegionalViewSource(reader, table)

    def latest_view(self, region_id: str, criterion_id: str) -> RegionalRunView | None:
        run_id = self.source.latest_id(region_id, criterion_id)
        return self.view(run_id) if run_id else None

    def view(self, run_id: str) -> RegionalRunView | None:
        return self.source.view(run_id)

    def rows(
        self,
        view: RegionalRunView,
        stage: RouteStage,
        page: int,
        page_size: int,
        sort: RowSort,
        descending: bool,
        search: str,
    ) -> RegionalRowPage:
        offset = (page - 1) * page_size
        if not self.source.normalized(view.run_id):
            result = self.legacy_rows(view.run_id, stage)
            if search:
                needle = search.casefold()
                result = [
                    row
                    for row in result
                    if needle in row.name.casefold() or needle in row.id.casefold()
                ]
            result = sort_rows(result, sort, descending, view.unit)
            return RegionalRowPage(
                view.run_id,
                stage,
                result[offset : offset + page_size],
                len(result),
                page,
                page_size,
            )
        where = "run_id={run:String} AND stage={stage:String}"
        params = {"run": view.run_id, "stage": stage, "search": search}
        if search:
            where += " AND positionCaseInsensitiveUTF8(concat(name,' ',id),{search:String})>0"
        total = (
            int(
                self.reader.rows(
                    f"SELECT count() AS n FROM {self.table}_rows WHERE {where}", params
                )[0]["n"]
            )
            if search
            else view.origins
        )
        order = {"position": "position", "name": "name", "cost": cost_column(view)}[sort]
        direction = "DESC" if descending else "ASC"
        columns = ",".join(
            name for name in SCHEMAS["run_rows"].names if name not in {"run_id", "stage"}
        )
        records = self.reader.arrow(
            f"SELECT {columns} FROM {self.table}_rows WHERE run_id={{run:String}} AND stage={{stage:String}} AND position IN (SELECT position FROM {self.table}_rows WHERE {where} ORDER BY {order} {direction} NULLS LAST,position LIMIT {{limit:UInt32}} OFFSET {{offset:UInt64}}) ORDER BY {order} {direction} NULLS LAST,position",
            {**params, "limit": page_size, "offset": offset},
        ).to_pylist()
        return RegionalRowPage(
            view.run_id, stage, [access_row(row) for row in records], total, page, page_size
        )

    def facilities(
        self, view: RegionalRunView, page: int, page_size: int, search: str
    ) -> RegionalFacilityPage:
        offset = (page - 1) * page_size
        if not self.source.normalized(view.run_id):
            records = self.source.legacy_record(view.run_id)["facilities"]
            items = [
                facility(row)
                for row in records
                if not search
                or search.casefold()
                in (row["name"] + " " + row["address"] + " " + row["id"]).casefold()
            ]
            return RegionalFacilityPage(
                view.run_id, items[offset : offset + page_size], len(items), page, page_size
            )
        where = "run_id={run:String}"
        params = {"run": view.run_id, "search": search}
        if search:
            where += " AND positionCaseInsensitiveUTF8(concat(name,' ',address,' ',id),{search:String})>0"
        total = (
            int(
                self.reader.rows(
                    f"SELECT count() AS n FROM {self.table}_facilities WHERE {where}", params
                )[0]["n"]
            )
            if search
            else view.facility_count
        )
        columns = ",".join(name for name in SCHEMAS["run_facilities"].names if name != "run_id")
        found = self.reader.arrow(
            f"SELECT {columns} FROM {self.table}_facilities WHERE {where} ORDER BY position LIMIT {{limit:UInt32}} OFFSET {{offset:UInt64}}",
            {**params, "limit": page_size, "offset": offset},
        ).to_pylist()
        return RegionalFacilityPage(
            view.run_id, [facility(row) for row in found], total, page, page_size
        )

    def point(
        self, view: RegionalRunView, stage: RouteStage, origin_id: str
    ) -> RegionalPointDetail | None:
        if not self.source.normalized(view.run_id):
            row = next((r for r in self.legacy_rows(view.run_id, stage) if r.id == origin_id), None)
            if row is None:
                return None
            target = next(
                (
                    facility(r)
                    for r in self.source.legacy_record(view.run_id)["facilities"]
                    if r["id"] == row.facility_id
                ),
                None,
            )
            return RegionalPointDetail(row, target)
        params = {"run": view.run_id, "stage": stage, "origin": origin_id}
        columns = ",".join(
            name for name in SCHEMAS["run_rows"].names if name not in {"run_id", "stage"}
        )
        records = self.reader.arrow(
            f"SELECT {columns} FROM {self.table}_rows WHERE run_id={{run:String}} AND stage={{stage:String}} AND id={{origin:String}} LIMIT 1",
            params,
        ).to_pylist()
        if not records:
            return None
        row = access_row(records[0])
        columns = ",".join(name for name in SCHEMAS["run_facilities"].names if name != "run_id")
        targets = self.reader.arrow(
            f"SELECT {columns} FROM {self.table}_facilities WHERE run_id={{run:String}} AND id={{target:String}} LIMIT 1",
            {"run": view.run_id, "target": row.facility_id or ""},
        ).to_pylist()
        return RegionalPointDetail(row, facility(targets[0]) if targets else None)

    def map_view(
        self, view: RegionalRunView, stage: RouteStage, bounds: RegionalMapBounds, zoom: int
    ) -> RegionalMapView:
        return RegionalViewMap(self.reader, self.source).read(view, stage, bounds, zoom)

    def legacy_rows(self, run_id: str, stage: RouteStage) -> list[AccessRow]:
        record = self.source.legacy_record(run_id)
        return [
            access_row(row) for row in record["baseline_rows" if stage == "baseline" else "rows"]
        ]


def cost_column(view: RegionalRunView) -> str:
    return "distance_metres" if view.unit == "metres" else "minutes"


def sort_rows(rows: list[AccessRow], sort: RowSort, descending: bool, unit: str) -> list[AccessRow]:
    if sort == "position":
        return list(reversed(rows)) if descending else rows
    if sort == "name":
        return sorted(rows, key=lambda row: row.name, reverse=descending)

    def cost(row: AccessRow) -> float | None:
        return row.distance_metres if unit == "metres" else row.minutes

    present = [row for row in rows if cost(row) is not None]
    missing = [row for row in rows if cost(row) is None]
    return sorted(present, key=lambda row: cost(row) or 0, reverse=descending) + missing
