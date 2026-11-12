from typing import Any, Literal

from app.domain.errors import DataUnavailable
from app.domain.region_names import canonical_region
from app.domain.settlement_names import (
    matching_places,
    normalized_place,
    settlement_name,
    settlement_query,
)
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_queries import ARRAYS, QUERIES
from app.usecase.graph_snapshot import GraphParameters, GraphQuery


class ClickHouseGraphSnapshot:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        rows = reader.rows(
            "SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_revision'", {}
        )
        if len(rows) != 1:
            raise DataUnavailable("Graph snapshot metadata is missing; import the dataset")
        self._revision = str(rows[0]["value"])
        self._regions: list[str] | None = None

    @property
    def revision(self) -> str:
        return self._revision

    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
        table = self.reader.arrow(ARRAYS[name], {})
        return {column: table[column].to_numpy() for column in table.column_names}

    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]:
        parameters = dict(parameters or {})
        place_query = ""
        if query in ("locations", "corridor_places"):
            needle = str(parameters.pop("query")).lower()
            if query == "corridor_places":
                needle = self._qualified(needle)
                place_query = needle
                needle = settlement_name(settlement_query(needle)[0])
            parameters["pattern"] = (
                "%" + needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            )
        rows = self._rows(query, parameters)
        if query == "corridor_places":
            return self._places(rows, place_query, parameters)
        return rows

    def _qualified(self, query: str) -> str:
        name, _, region = query.partition(",")
        if not region.strip():
            return query
        if self._regions is None:
            self._regions = [str(r[0]) for r in self._rows("region_list", {})]
        canonical = canonical_region(region, self._regions)
        return f"{name}, {canonical}" if canonical else query

    def _rows(self, query: GraphQuery, parameters: GraphParameters) -> list[tuple[Any, ...]]:
        ids = parameters.get("ids")
        if query == "candidates" and isinstance(ids, list) and len(ids) > 5000:
            unique_ids = list(dict.fromkeys(int(value) for value in ids))
            return [
                row
                for start in range(0, len(unique_ids), 5000)
                for row in self._rows(
                    query, {**parameters, "ids": unique_ids[start : start + 5000]}
                )
            ]
        table = self.reader.arrow(QUERIES[query], parameters)
        return list(zip(*(table[c].to_pylist() for c in table.column_names), strict=True))

    def _places(
        self, rows: list[tuple[Any, ...]], place_query: str, parameters: GraphParameters
    ) -> list[tuple[Any, ...]]:
        places = [(str(r[1]), str(r[2])) for r in rows]
        indices = matching_places(places, place_query)
        name = settlement_query(place_query)[0]
        if any(normalized_place(places[i][0]) == name for i in indices):
            return [rows[i] for i in indices]
        markets = self._rows("market_places", {"pattern": parameters["pattern"]})
        chosen = matching_places([(str(r[1]), str(r[2])) for r in markets], place_query)
        if chosen:
            return [markets[i] for i in chosen]
        return [rows[i] for i in indices]
