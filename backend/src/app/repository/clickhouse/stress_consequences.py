from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.stress_consequence_queries import (
    DESTINATIONS,
    EXAMPLES,
    NEARBY,
    POINTS,
)
from app.usecase.road_consequences import (
    ConnectionConsequence,
    DelayExposure,
    DestinationConsequence,
    NearbyAccessChange,
    RegionalConsequences,
)


def average(total: float, count: int) -> float | None:
    return float(total) / count if count else None


def regional_consequences(
    reader: ClickHouseReader,
    job_id: str,
    region: str,
) -> RegionalConsequences:
    parameters = {"id": job_id, "region": region}
    points = reader.rows(POINTS, parameters)[0]
    nearby = reader.rows(NEARBY, parameters)[0]
    comparable = int(nearby["comparable"])
    destinations = [
        DestinationConsequence(
            str(row["destination"]),
            int(row["settlements"]),
            int(row["residents"]),
            int(row["lost"]),
            int(row["lost_residents"]),
            int(row["nearby_residents"]),
            int(row["comparable"]),
            average(row["before_sum"], int(row["comparable"])),
            average(row["after_sum"], int(row["comparable"])),
        )
        for row in reader.rows(DESTINATIONS, parameters)
    ]
    examples = [
        ConnectionConsequence(
            str(row["point_id"]),
            str(row["name"]),
            int(row["population"]),
            str(row["destination"]),
            float(row["before_minutes"]),
            float(row["after_minutes"]) if row["after_minutes"] is not None else None,
            float(row["added_minutes"]) if row["added_minutes"] is not None else None,
        )
        for row in reader.rows(EXAMPLES, parameters)
    ]
    return RegionalConsequences(
        region,
        int(points["lost_connections"]),
        int(points["losing_settlements"]),
        int(points["losing_residents"]),
        [
            DelayExposure(t, int(points[f"delay{t}_points"]), int(points[f"delay{t}_residents"]))
            for t in (30, 60, 120)
        ],
        NearbyAccessChange(
            2,
            int(nearby["changed"]),
            int(nearby["lost"]),
            comparable,
            average(nearby["before_sum"], comparable),
            average(nearby["after_sum"], comparable),
            average(nearby["after_sum"] - nearby["before_sum"], comparable),
            int(nearby["crossing"]),
            int(points["crossing_points"]),
            int(points["crossing_residents"]),
        ),
        destinations,
        examples,
    )
