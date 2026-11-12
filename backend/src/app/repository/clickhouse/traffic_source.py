import json
from hashlib import sha256
from math import cos, isfinite, radians
from pathlib import Path

import pyarrow.parquet as pq

from app.domain.errors import InvalidQuery
from app.repository.clickhouse.client import ClickHouseReader, QueryValue
from app.usecase.traffic import TrafficScope


class ClickHouseTrafficSource:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def resolve(self, scope: TrafficScope) -> list[float]:
        if scope.focus_bounds:
            focus = validate_bounds(scope.focus_bounds)
            if not scope.bounds:
                latitude = max(abs(focus[1]), abs(focus[3]))
                margin = 20 / (111 * max(0.1, cos(radians(latitude))))
                return validate_bounds([max(-180, focus[0] - margin), max(-90, focus[1] - 20 / 111),
                                        min(180, focus[2] + margin), min(90, focus[3] + 20 / 111)])
        if scope.bounds:
            outer = validate_bounds(scope.bounds)
            if scope.focus_bounds and not (outer[0] <= focus[0] < focus[2] <= outer[2]
                                           and outer[1] <= focus[1] < focus[3] <= outer[3]):
                raise InvalidQuery("Focus bounds must lie inside the context bounds")
            return outer
        rows = []
        if scope.places:
            for place in scope.places:
                matches = self.reader.rows(
                    "SELECT point_id,any(lat) lat,any(lon) lon FROM plexus_graph.locations "
                    "WHERE (lowerUTF8(settlement)=lowerUTF8({place:String}) OR point_id={place:String}) "
                    "AND ({region:String}='' OR lowerUTF8(region)=lowerUTF8({region:String})) "
                    "GROUP BY point_id LIMIT 3",
                    {"place": place, "region": scope.region},
                )
                if len(matches) != 1:
                    raise InvalidQuery(
                        "Place is missing or ambiguous; qualify by exact region or point ID"
                    )
                rows.extend(matches)
        elif scope.region or scope.regions:
            rows = self.reader.rows(
                "SELECT lat,lon FROM plexus_graph.locations WHERE lowerUTF8(region) IN {regions:Array(String)}",
                {"regions": [name.casefold() for name in (scope.regions or [scope.region])]},
            )
        if not rows:
            raise InvalidQuery("Use one city, two exact settlement names, region names or geographic bounds")
        latitude = max(abs(float(row["lat"])) for row in rows)
        margin = 20 / (111 * max(0.1, cos(radians(latitude))))
        return validate_bounds(
            [
                max(-180, min(float(row["lon"]) for row in rows) - margin),
                max(-90, min(float(row["lat"]) for row in rows) - 20 / 111),
                min(180, max(float(row["lon"]) for row in rows) + margin),
                min(90, max(float(row["lat"]) for row in rows) + 20 / 111),
            ]
        )

    def inventory(self) -> str:
        rows = self.reader.rows(
            "SELECT count() residential_objects FROM plexus_synthetic_traffic.housing_current", {}
        )
        sources = self.reader.rows(
            "SELECT record FROM plexus_synthetic_traffic.housing_collections ORDER BY collection_id DESC LIMIT 1",
            {},
        )
        return json.dumps(
            {
                **rows[0],
                "collection": json.loads(sources[0]["record"]) if sources else None,
                "coverage": "Russian Federation residential OSM objects; not observed traffic",
                "runtime": "bounded windows up to 2000000 directed edges, 128 demand zones; nationwide inventory, local assignment",
                "calculate": "calculate_scenario(kind=traffic_development)",
            },
            ensure_ascii=False,
        )

    def export(self, bounds: list[float], destination: Path) -> None:
        validate_bounds(bounds)
        parameters: dict[str, QueryValue] = dict(zip(["w", "s", "e", "n"], bounds, strict=True))
        box = "lon BETWEEN {w:Float64} AND {e:Float64} AND lat BETWEEN {s:Float64} AND {n:Float64}"
        nodes = "SELECT node FROM plexus_graph.nodes WHERE " + box
        revision = "SELECT key,value FROM plexus_atlas.atlas_metadata WHERE key IN ('graph_revision','road_cost_model_version') ORDER BY key"
        before = self.reader.rows(revision, {})
        columns = {row["name"] for row in self.reader.rows("DESCRIBE TABLE plexus_graph.ways", {})}
        season = "AND w.operating_season='all'" if "operating_season" in columns else ""
        edges = self.reader.arrow(
            "SELECT e.src src,e.dst dst,e.km km,w.way_id way_id,e.km/c.freeflow_speed_kmh free_hours,"
            "c.capacity_pcu_h capacity,c.lane_basis LIKE '%shared%' shared,"
            "w.highway IN ('residential','living_street','unclassified','service','tertiary','tertiary_link') access "
            "FROM plexus_graph.edges e INNER JOIN plexus_graph.ways w ON e.way_idx=w.way_idx "
            "INNER JOIN plexus_graph.road_costs c ON c.way_idx=e.way_idx WHERE NOT c.is_ferry "
            "AND c.capacity_pcu_h>0 AND c.freeflow_speed_kmh>0 AND e.km>0 "
            + season
            + f" AND e.src IN ({nodes}) AND e.dst IN ({nodes}) ORDER BY e.src,e.dst,w.way_id LIMIT 2000001",
            parameters,
        )
        if not 0 < edges.num_rows <= 2000000:
            raise InvalidQuery(
                "Traffic window is empty or exceeds 2000000 edges; select a smaller area"
            )
        homes = self.reader.arrow(
            "SELECT id,lat,lon,residential_m2_proxy,floors_assumed FROM plexus_synthetic_traffic.housing_current "
            "WHERE id IN (SELECT id FROM plexus_synthetic_traffic.housing WHERE "
            + box
            + ") AND "
            + box
            + " LIMIT 2000001",
            parameters,
        )
        if homes.num_rows > 2000000:
            raise InvalidQuery(
                "Traffic window exceeds 2000000 residential objects; select a smaller area"
            )
        destination.mkdir(parents=True, exist_ok=False)
        pq.write_table(edges, destination / "edges.parquet")
        pq.write_table(homes, destination / "housing.parquet")
        for name, query in [
            (
                "nodes",
                "SELECT node,lat,lon FROM plexus_graph.nodes WHERE " + box + " ORDER BY node",
            ),
            (
                "places",
                "SELECT point_id,settlement,region,population,node,lat,lon FROM plexus_graph.locations WHERE "
                + box
                + " ORDER BY point_id",
            ),
        ]:
            pq.write_table(self.reader.arrow(query, parameters), destination / f"{name}.parquet")
        if before != self.reader.rows(revision, {}):
            raise InvalidQuery("Road graph changed while reading; start a fresh calculation")
        sources = self.reader.rows(
            "SELECT source_id,record FROM plexus_synthetic_traffic.housing_sources ORDER BY source_id",
            {},
        )
        (destination / "source.json").write_text(
            json.dumps(
                {
                    "bounds": bounds,
                    "metadata": before,
                    "housing_sources": sources,
                    "sha256": {
                        p.name: sha256(p.read_bytes()).hexdigest()
                        for p in destination.glob("*.parquet")
                    },
                },
                ensure_ascii=False,
            )
        )


def validate_bounds(bounds: list[float]) -> list[float]:
    if (
        len(bounds) != 4
        or any(not isfinite(v) for v in bounds)
        or not -180 <= bounds[0] < bounds[2] <= 180
        or not -90 <= bounds[1] < bounds[3] <= 90
    ):
        raise InvalidQuery("Use ordered west,south,east,north geographic bounds")
    return bounds
