from dataclasses import fields
from typing import Any

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
        inventory = [inventory_facility(row, category) for row in rows]

        combined = {facility.id: facility for facility in inventory}
        combined.update(
            {facility.id: facility for facility in self.directory_candidates(region_id, category)}
        )
        return sorted(combined.values(), key=lambda facility: (facility.name, facility.id))

    def routing_candidates(self, category: str) -> list[Facility]:
        regions = self.reader.rows(
            "SELECT DISTINCT id FROM plexus_normative.inventory_regions FINAL ORDER BY id", {}
        )
        official = self.service_directories.latest_by_region(category)
        grouped: dict[str, dict[str, Facility]] = {str(region["id"]): {} for region in regions}
        rows = self.reader.rows(
            f"SELECT region_id,id,name,address,latitude,longitude,source_url,snapshot_url,source_sha256,observed_at "
            f"FROM {self.inventory_table} FINAL WHERE has(categories,{{category:String}}) ORDER BY name,id",
            {"category": category},
        )
        for row in rows:
            region = str(row["region_id"])
            if region in grouped and region not in official:
                facility = inventory_facility(row, category)
                grouped[region][facility.id] = facility
        columns = ",".join(f"f.{field.name} AS {field.name}" for field in fields(Facility))
        rows = self.reader.rows(
            f"SELECT membership.region_id AS membership_region,{columns} FROM {self.facility_table} AS f "
            f"INNER JOIN (SELECT region_id,facility_id,service FROM {self.directory_table} FINAL "
            "WHERE category={category:String}) AS membership ON f.id=membership.facility_id AND f.service=membership.service "
            "ORDER BY f.name,f.id", {"category": category},
        )
        for row in rows:
            region = str(row.pop("membership_region"))
            if region in grouped and region not in official:
                facility = Facility(**row)
                grouped[region][facility.id] = facility
        combined = {}
        for region, facilities in grouped.items():
            for facility in official.get(region, list(facilities.values())):
                combined[(facility.service, facility.id)] = facility
        return sorted(combined.values(), key=lambda facility: (facility.name, facility.id))

    def directory_candidates(self, region_id: str, category: str) -> list[Facility]:
        columns = ",".join(f"f.{field.name} AS {field.name}" for field in fields(Facility))
        rows = self.reader.rows(
            f"SELECT {columns} FROM {self.facility_table} AS f INNER JOIN (SELECT facility_id,service FROM {self.directory_table} FINAL WHERE region_id={{region:String}} AND category={{category:String}}) AS membership ON f.id=membership.facility_id AND f.service=membership.service ORDER BY f.name,f.id",
            {"region": region_id, "category": category},
        )
        return [Facility(**row) for row in rows]


def inventory_facility(row: dict[str, Any], category: str) -> Facility:
    return Facility(
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
