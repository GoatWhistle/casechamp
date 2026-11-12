from app.domain.normative.fire_destination import FireDestination
from app.repository.clickhouse.client import ClickHouseReader

DESTINATION_COLUMNS = "id,name,address,region,latitude,longitude,source_url,observed_at,reference_status,source_sha256"


class FireDestinations:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def current(self, region: str) -> list[FireDestination]:
        rows = self.reader.rows(
            f"SELECT {DESTINATION_COLUMNS} FROM plexus_normative.fire_destinations WHERE region={{region:String}} ORDER BY id",
            {"region": region},
        )
        return [FireDestination(**row) for row in rows]
