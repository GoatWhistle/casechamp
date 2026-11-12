from collections.abc import Mapping
from dataclasses import replace
from typing import Any
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings
from tests.unit.domain.normative.fire_evidence.factories import profile
from tests.unit.usecase.test_fire_object_assessment import objects

from app.repository.clickhouse.client import ClickHouseReader, QueryValue
from app.repository.clickhouse.normative import ClickHouseNormativeRepository
from app.repository.clickhouse.normative_schema import SCHEMAS
from app.repository.clickhouse.normative_store import NormativeStore


class SnapshotReader(ClickHouseReader):
    def __init__(self, reader: ClickHouseReader, tables: dict[str, str]) -> None:
        self.original = reader
        self.tables = tables
        super().__init__(
            reader.url, reader.headers["X-ClickHouse-User"], reader.headers["X-ClickHouse-Key"]
        )

    def rows(self, sql: str, parameters: Mapping[str, QueryValue]) -> list[dict[str, Any]]:
        for name, target in self.tables.items():
            sql = sql.replace("plexus_normative." + name, "plexus_normative." + target)
        return self.original.rows(sql, parameters)


class SnapshotStore(NormativeStore):
    def __init__(self, reader: ClickHouseReader, tables: dict[str, str]) -> None:
        self.tables = tables
        super().__init__(reader)

    def insert(self, table: str, rows: list[dict[str, object]]) -> None:
        super().insert(self.tables[table], rows)


def test_arbitrary_object_snapshot_replays_without_live_registry_or_settlement_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    names = [
        "runs",
        "run_rows",
        "run_facilities",
        "run_fire_destinations",
        "run_fire_facts",
        "run_criteria",
        "run_rule_sets",
    ]
    prefix = "test_object_" + uuid4().hex + "_"
    tables = {name: prefix + name for name in names}
    created = []

    def command(sql: str) -> None:
        request = Request(
            reader.url + "/",
            data=sql.encode(),
            headers={k: v for k, v in reader.headers.items() if k != "Accept-Encoding"},
        )
        with urlopen(request, timeout=30) as response:
            response.read()

    try:
        for name, table in tables.items():
            command(f"CREATE TABLE plexus_normative.{table} AS plexus_normative.{name}")
            created.append(table)
            monkeypatch.setitem(SCHEMAS, table, SCHEMAS[name])
        usecase, repository = objects()
        repository.facilities.return_value = [
            replace(
                item,
                source_sha256="ef" * 32,
                coordinate_snapshot_sha256="cd" * 32,
                coordinate_snapshot_url="https://example.org/frozen.osm.pbf",
            )
            for item in repository.facilities.return_value
        ]
        scoped = ClickHouseNormativeRepository(SnapshotReader(reader, tables))
        repository.save.side_effect = SnapshotStore(reader, tables).save
        repository.latest.side_effect = scoped.latest
        repository.route_context.side_effect = scoped.route_context
        result = usecase.assess("N03", [], profile(), "fire_objects")
        assert result.run_id is not None
        repository.fire_destinations.return_value = []
        repository.facilities.return_value = []
        restored = usecase.latest("N03")
        assert restored is not None
        assert restored.rows == result.rows
        assert sorted(restored.facilities, key=lambda item: item.id) == sorted(
            result.facilities, key=lambda item: item.id
        )
        assert all(item.coordinate_snapshot_sha256 == "cd" * 32 for item in restored.facilities)
        assert all(item.source_sha256 == "ef" * 32 for item in restored.facilities)
        assert restored.origin_basis == "fire_objects"
        assert restored.qualification_as_of == result.qualification_as_of
        assert restored.rows[0].state == "within"
        trace = usecase.route(result.run_id, "site-42", "scenario")
        assert trace.geometry.minutes == result.rows[0].minutes
        assert trace.geometry.approaches[-1][-1] == (
            result.rows[0].longitude,
            result.rows[0].latitude,
        )
        assert (
            int(
                reader.rows("SELECT count() AS n FROM plexus_normative.fire_destinations", {})[0][
                    "n"
                ]
            )
            == 0
        )
        source = reader.rows(
            f"SELECT source_sha256,reference_status FROM plexus_normative.{tables['run_fire_destinations']}",
            {},
        )
        assert source == [{"source_sha256": "ab" * 32, "reference_status": "verified_object"}]
        repository.origins.assert_not_called()
    finally:
        for table in reversed(created):
            command(f"DROP TABLE plexus_normative.{table} SYNC")
