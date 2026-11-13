from app.domain.errors import DataUnavailable
from app.domain.normative.model import Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_snapshots import RegionalSnapshots


class ServiceDirectories:
    def __init__(
        self, reader: ClickHouseReader, prefix: str = "plexus_normative.service_directories"
    ) -> None:
        self.reader = reader
        self.prefix = prefix

    def latest_by_region(self, category: str) -> dict[str, list[Facility]]:
        rows = self.reader.rows(
            f"SELECT region_id,id,facilities,source_sha256 FROM {self.prefix} "
            "WHERE category={category:String} ORDER BY observed_at DESC,id DESC LIMIT 1 BY region_id",
            {"category": category},
        )
        result = {}
        for head in rows:
            facilities = [Facility(**row) for row in RegionalSnapshots(self.reader, self.prefix).load(
                head["id"], "facilities", head["facilities"])]
            if any(f.source_sha256 != head["source_sha256"] for f in facilities):
                raise DataUnavailable("The service directory differs from its source snapshot")
            result[str(head["region_id"])] = facilities
        return result

    def latest(self, region_id: str, category: str) -> list[Facility] | None:
        rows = self.reader.rows(
            f"SELECT id,facilities,source_sha256 FROM {self.prefix} "
            "WHERE region_id={region:String} AND category={category:String} "
            "ORDER BY observed_at DESC,id DESC LIMIT 1",
            {"region": region_id, "category": category},
        )
        if not rows:
            return None
        head = rows[0]
        facilities = [
            Facility(**row)
            for row in RegionalSnapshots(self.reader, self.prefix).load(
                head["id"], "facilities", head["facilities"]
            )
        ]
        if any(f.source_sha256 != head["source_sha256"] for f in facilities):
            raise DataUnavailable("The service directory differs from its source snapshot")
        return facilities
