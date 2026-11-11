import json
from collections.abc import Iterator
from dataclasses import asdict
from time import time_ns

from app.repository.clickhouse.client import ClickHouseReader, QueryValue
from app.repository.clickhouse.stress_consequences import regional_consequences
from app.repository.clickhouse.writer import ClickHouseWriter
from app.usecase.road_consequences import RegionalConsequences
from app.usecase.road_stress import (
    StressImpact,
    StressJob,
    StressMarketChange,
    StressPoint,
    StressRegion,
    StressTotals,
)


class ClickHouseStressStore:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self.writer = ClickHouseWriter(reader)

    def consequences(self, job_id: str, region: str) -> RegionalConsequences:
        return regional_consequences(self.reader, job_id, region)

    def totals(self, job_id: str, region: str = "") -> StressTotals:
        row = self.reader.rows(
            "SELECT count() AS affected_points, sum(population) AS exposed_population, "
            "countIf(external_isolation) AS isolated_points, "
            "sumIf(population,external_isolation) AS isolated_population, "
            "maxOrDefault(delay_minutes) AS max_delay_minutes, uniqExact(region) AS affected_regions "
            "FROM plexus_state.stress_point_impacts FINAL "
            "WHERE job_id={id:String} AND ({region:String}='' OR region={region:String})",
            {"id": job_id, "region": region},
        )[0]
        return StressTotals(
            int(row["affected_points"]), int(row["exposed_population"]),
            int(row["isolated_points"]), int(row["isolated_population"]),
            float(row["max_delay_minutes"]), int(row["affected_regions"]),
        )

    def baseline(self, version: str) -> Iterator[tuple[int, list[float]]]:
        table = self.reader.arrow(
            "SELECT market,times FROM plexus_state.stress_baseline FINAL WHERE version={version:String} ORDER BY market",
            {"version": version},
        )
        for market, times in zip(table["market"], table["times"], strict=True):
            yield int(market.as_py()), times.as_py()

    def save_baseline(self, version: str, market: int, times: list[float]) -> None:
        self.writer.insert("stress_baseline", {"version": version, "market": market,
                                              "times": times, "updated": time_ns()})

    def points(self) -> list[StressPoint]:
        rows = self.reader.rows(
            "SELECT point_id,any(settlement) name,any(region) region,"
            "max(coalesce(population,0)) population,any(node) node,any(snap_km) snap_km,"
            "any(lon) lon,any(lat) lat FROM plexus_graph.locations GROUP BY point_id "
            "ORDER BY point_id", {},
        )
        return [StressPoint(str(r["point_id"]), str(r["name"] or r["point_id"]),
                            str(r["region"] or ""), int(r["population"]),
                            int(r["node"]) if r["node"] is not None else -1,
                            float(r["snap_km"] or 0), float(r["lon"] or 0),
                            float(r["lat"] or 0)) for r in rows]

    def save(self, job: StressJob) -> None:
        self.writer.insert("stress_jobs", {
            "id": job.id, "payload": json.dumps(asdict(job), allow_nan=False),
            "updated": time_ns(),
        })

    def load(self) -> list[StressJob]:
        rows = self.reader.rows(
            "SELECT payload FROM plexus_state.stress_jobs FINAL ORDER BY updated", {}
        )
        result = []
        for row in rows:
            value = json.loads(row["payload"])
            value["regions"] = [StressRegion(**r) for r in value["regions"]]
            result.append(StressJob(**value))
        return result

    def save_impacts(self, job_id: str, impacts: list[StressImpact]) -> None:
        for start in range(0, len(impacts), 1000):
            rows: list[dict[str, object]] = []
            for impact in impacts[start:start + 1000]:
                point = impact.point
                rows.append({
                    "job_id": job_id, "point_id": point.id, "name": point.name,
                    "region": point.region, "population": max(0, point.population),
                    "node": point.node, "snap_km": point.snap_km,
                    "longitude": point.longitude, "latitude": point.latitude,
                    "lost_markets": impact.lost_markets,
                    "external_isolation": impact.external_isolation,
                    "delay_minutes": impact.delay_minutes, "worst_market": impact.worst_market,
                    "markets": [m.market for m in impact.markets],
                    "before_hours": [m.before_hours for m in impact.markets],
                    "after_hours": [m.after_hours for m in impact.markets], "updated": time_ns(),
                })
            self.writer.insert_many("stress_point_impacts", rows)

    def impacts(self, job_id: str, region: str = "", offset: int = 0, limit: int = 200,
                bounds: tuple[float, float, float, float] | None = None) -> list[StressImpact]:
        params: dict[str, QueryValue] = {"id": job_id, "region": region, "offset": offset, "limit": limit}
        where = "job_id={id:String} AND ({region:String}='' OR region={region:String})"
        if bounds:
            params.update(dict(zip(("west", "south", "east", "north"), bounds, strict=True)))
            where += " AND longitude BETWEEN {west:Float64} AND {east:Float64} AND latitude BETWEEN {south:Float64} AND {north:Float64}"
        rows = self.reader.rows(
            "SELECT point_id,name,region,population,node,snap_km,longitude,latitude,"
            "lost_markets,external_isolation,delay_minutes,worst_market,markets,before_hours,after_hours "
            "FROM plexus_state.stress_point_impacts FINAL WHERE " + where +
            " ORDER BY external_isolation DESC,delay_minutes DESC,point_id LIMIT {limit:UInt32} OFFSET {offset:UInt32}", params,
        )
        return [StressImpact(
            StressPoint(str(r["point_id"]), str(r["name"]), str(r["region"]), int(r["population"]),
                        int(r["node"]), float(r["snap_km"]), float(r["longitude"]), float(r["latitude"])),
            int(r["lost_markets"]), bool(r["external_isolation"]), float(r["delay_minutes"]), str(r["worst_market"]),
            [StressMarketChange(str(m), float(a), float(b) if b is not None else None)
             for m, a, b in zip(r["markets"], r["before_hours"], r["after_hours"], strict=True)],
        ) for r in rows]
