from dataclasses import fields

from app.domain.normative.model import Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.service_directories import ServiceDirectories


class ClickHouseRegionalCatalogRepository:
    def __init__(
        self,
        reader: ClickHouseReader,
        inventory_table: str = "plexus_normative.national_inventory",
        directory_table: str = "plexus_normative.regional_directory_memberships",
        facility_table: str = "plexus_normative.facilities",
        service_directory_prefix: str = "plexus_normative.service_directories",
    ) -> None:
        self.reader = reader
        self.inventory_table = inventory_table
        self.directory_table = directory_table
        self.facility_table = facility_table
        self.service_directories = ServiceDirectories(reader, service_directory_prefix)

    def region_name(self, region_id: str) -> str | None:
        rows = self.reader.rows(
            "SELECT name FROM plexus_normative.inventory_regions FINAL WHERE id={region:String} LIMIT 1",
            {"region": region_id},
        )
        return str(rows[0]["name"]) if rows else None

    def walking_available(self, region_id: str) -> bool:
        return bool(
            self.reader.rows(
                "SELECT revision FROM plexus_normative.pedestrian_regions "
                "WHERE region_id={region:String} AND purpose='physical' LIMIT 1",
                {"region": region_id},
            )
        )

    def candidates(self, region_id: str, category: str) -> list[Facility]:
        official = self.service_directories.latest(region_id, category)
        if official is not None:
            return official
        rows = self.reader.rows(
            f"""SELECT id,name,address,latitude,longitude,source_url,
        snapshot_url,source_sha256,observed_at FROM {self.inventory_table} FINAL
        WHERE region_id={{region:String}} AND has(categories,{{category:String}}) ORDER BY name,id""",
            {"region": region_id, "category": category},
        )
        inventory = [
            Facility(
                id=row["id"],
                service=category,
                name=row["name"],
                address=row["address"],
                source_url=row["snapshot_url"],
                observed_at=row["observed_at"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                coordinate_source=row["source_url"],
                coordinate_status="osm_institution_pin",
                source_sha256=row["source_sha256"],
                coordinate_snapshot_sha256=row["source_sha256"],
                coordinate_snapshot_url=row["snapshot_url"],
            )
            for row in rows
        ]

        combined = {facility.id: facility for facility in inventory}
        combined.update(
            {facility.id: facility for facility in self.directory_candidates(region_id, category)}
        )
        return sorted(combined.values(), key=lambda facility: (facility.name, facility.id))

    def directory_candidates(self, region_id: str, category: str) -> list[Facility]:
        columns = ",".join(f"f.{field.name} AS {field.name}" for field in fields(Facility))
        rows = self.reader.rows(
            f"SELECT {columns} FROM {self.facility_table} AS f INNER JOIN (SELECT facility_id,service FROM {self.directory_table} FINAL WHERE region_id={{region:String}} AND category={{category:String}}) AS membership ON f.id=membership.facility_id AND f.service=membership.service ORDER BY f.name,f.id",
            {"region": region_id, "category": category},
        )
        return [Facility(**row) for row in rows]
