import json
from dataclasses import asdict, replace
from urllib.request import Request, urlopen
from uuid import uuid4

from tests.storage import settings
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_catalog import ClickHouseRegionalCatalogRepository


def test_explicit_regional_directory_adds_missing_geometry_and_provenance_without_region_leak() -> (
    None
):
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password, max_threads=1
    )
    prefix = "plexus_normative.test_directory_" + uuid4().hex
    tables = {
        "inventory": prefix + "_inventory",
        "directory": prefix + "_membership",
        "facilities": prefix + "_facilities",
    }

    def command(sql: str) -> None:
        with urlopen(
            Request(reader.url + "/", data=sql.encode(), headers=reader.headers), timeout=60
        ) as response:
            response.read()

    command(f"CREATE TABLE {tables['inventory']} AS plexus_normative.national_inventory")
    command(
        f"CREATE TABLE {tables['directory']} AS plexus_normative.regional_directory_memberships"
    )
    command(f"CREATE TABLE {tables['facilities']} AS plexus_normative.facilities")
    try:
        located = replace(
            facility(), id="directory-a", service="employment", source_sha256="a" * 64
        )
        missing = replace(
            located,
            id="directory-b",
            latitude=None,
            longitude=None,
            coordinate_source=None,
            coordinate_status="missing",
        )
        foreign = replace(located, id="foreign")
        command(
            f"INSERT INTO {tables['facilities']} FORMAT JSONEachRow\n"
            + "\n".join(json.dumps(asdict(f)) for f in (located, missing, foreign))
        )
        memberships = [
            {
                "region_id": region,
                "category": "employment_candidate",
                "service": f.service,
                "facility_id": f.id,
                "scope_source_url": f.source_url,
                "scope_source_sha256": f.source_sha256,
                "version": 1,
            }
            for region, f in [("R", located), ("R", missing), ("Other", foreign)]
        ]
        command(
            f"INSERT INTO {tables['directory']} FORMAT JSONEachRow\n"
            + "\n".join(json.dumps(r) for r in memberships)
        )
        osm = {
            "id": "osm-a",
            "region_id": "R",
            "region_name": "Region",
            "name": "OSM candidate",
            "address": "Address",
            "categories": ["employment_candidate"],
            "latitude": 55,
            "longitude": 65,
            "source_url": "https://osm.org/node/1",
            "snapshot_url": "https://example.org/source.pbf",
            "source_sha256": "b" * 64,
            "observed_at": "2026-11-12",
            "geometry_method": "osm_pin",
            "version": 1,
            "district": "test",
        }
        command(f"INSERT INTO {tables['inventory']} FORMAT JSONEachRow\n" + json.dumps(osm))
        repository = ClickHouseRegionalCatalogRepository(
            reader, tables["inventory"], tables["directory"], tables["facilities"]
        )
        result = repository.candidates("R", "employment_candidate")
        assert len(result) == 3
        by_id = {f.id: f for f in result}
        assert by_id[located.id] == located
        assert by_id[missing.id] == missing
        assert by_id["osm-a"].coordinate_snapshot_sha256 == "b" * 64
        assert foreign.id not in by_id
        assert repository.candidates("R", "medical") == []
        assert repository.candidates("Unknown", "employment_candidate") == []
        assert repository.candidates("Other", "employment_candidate") == [foreign]
    finally:
        for table in tables.values():
            command(f"DROP TABLE {table}")
