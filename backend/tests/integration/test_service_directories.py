import json
from dataclasses import replace
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_snapshots import RegionalSnapshots
from app.repository.clickhouse.service_directories import ServiceDirectories


def test_complete_directory_replaces_old_snapshot_and_unpublished_rows_remain_invisible() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password, max_threads=1
    )
    prefix = "plexus_normative.test_service_" + uuid4().hex

    def command(sql: str) -> None:
        with urlopen(
            Request(reader.url + "/", data=sql.encode(), headers=reader.headers), timeout=60
        ) as response:
            response.read()

    command(f"CREATE TABLE {prefix} AS plexus_normative.service_directories")
    command(f"CREATE TABLE {prefix}_facilities AS plexus_normative.service_directories_facilities")
    try:
        snapshots = RegionalSnapshots(reader, prefix)
        repository = ServiceDirectories(reader, prefix)
        first = replace(facility(), id="first", source_sha256="a" * 64)
        second = replace(first, id="second")
        snapshots.save_facilities("one", [first])
        header = {
            "id": "one",
            "region_id": "R",
            "category": "employment_candidate",
            "observed_at": "2026-11-12T01:00:00",
            "source_sha256": "a" * 64,
            "facilities": 1,
        }
        command(f"INSERT INTO {prefix} FORMAT JSONEachRow\n" + json.dumps(header))
        snapshots.save_facilities("two", [second])
        assert repository.latest("R", "employment_candidate") == [first]
        command(
            f"INSERT INTO {prefix} FORMAT JSONEachRow\n"
            + json.dumps({**header, "id": "two", "observed_at": "2026-11-12T02:00:00"})
        )
        assert repository.latest("R", "employment_candidate") == [second]
        assert repository.latest("Other", "employment_candidate") is None
        assert repository.latest("R", "medical") is None
        command(
            f"INSERT INTO {prefix} FORMAT JSONEachRow\n"
            + json.dumps({**header, "id": "broken", "observed_at": "2026-11-12T03:00:00"})
        )
        with pytest.raises(DataUnavailable, match="incomplete"):
            repository.latest("R", "employment_candidate")
    finally:
        command(f"DROP TABLE {prefix}")
        command(f"DROP TABLE {prefix}_facilities")
