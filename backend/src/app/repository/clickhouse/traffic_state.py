import json
from time import time_ns

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.records import decode, encode
from app.repository.clickhouse.writer import ClickHouseWriter
from app.usecase.traffic import TrafficJob


class ClickHouseTrafficStore:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self.writer = ClickHouseWriter(reader)

    def load(self) -> list[TrafficJob]:
        rows = self.reader.rows(
            "SELECT payload FROM plexus_state.traffic_jobs FINAL ORDER BY updated DESC LIMIT 100",
            {},
        )
        jobs = []
        for row in reversed(rows):
            payload = json.loads(row["payload"])
            payload.setdefault("indices", [])
            for baseline in payload.get("baseline") or []:
                baseline.setdefault("mean_trip_minutes", None)
            for alternative in payload["alternatives"]:
                alternative.setdefault("indices", [])
                alternative.setdefault("road_names", [])
                alternative.setdefault("housing_clearance", None)
                alternative["after"].setdefault("mean_trip_minutes", None)
            jobs.append(decode(TrafficJob, payload))
        return jobs

    def save(self, job: TrafficJob) -> None:
        self.writer.insert(
            "traffic_jobs",
            {
                "id": job.id,
                "payload": json.dumps(encode(TrafficJob, job), allow_nan=False),
                "updated": time_ns(),
            },
        )
