from dataclasses import asdict, fields
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings
from tests.unit.domain.normative.fire_evidence.factories import facts as fire_facts
from tests.unit.domain.normative.library.factories import facts
from tests.unit.domain.normative.medical.factories import facts as medical_facts

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative_schema import SCHEMAS
from app.repository.clickhouse.normative_store import NormativeStore


@pytest.mark.parametrize("kind", ["library", "medical", "fire"])
def test_typed_transport_evidence_roundtrips_in_an_isolated_table(
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url,
        config.clickhouse_user,
        config.clickhouse_password,
    )
    table = "test_transport_evidence_" + uuid4().hex

    def command(sql: str) -> None:
        request = Request(
            reader.url + "/",
            data=sql.encode(),
            headers={k: v for k, v in reader.headers.items() if k != "Accept-Encoding"},
        )
        with urlopen(request, timeout=30) as response:
            response.read()

    command(f"CREATE TABLE plexus_normative.{table} AS plexus_normative.run_{kind}_facts")
    try:
        monkeypatch.setitem(SCHEMAS, table, SCHEMAS[f"run_{kind}_facts"])
        original = (
            fire_facts() if kind == "fire" else medical_facts() if kind == "medical" else facts()
        )
        NormativeStore(reader).insert(table, [{"run_id": "test", **asdict(original)}])
        columns = ",".join(field.name for field in fields(type(original)))
        records = reader.rows(f"SELECT {columns} FROM plexus_normative.{table}", {})
        assert len(records) == 1
        restored = records[0]
        for key in ("eligible_facility_ids", "verified_closed_way_ids"):
            restored[key] = tuple(restored[key])
        assert type(original)(**restored) == original
        assert reader.rows(f"SELECT count() AS n FROM plexus_normative.{kind}_facts", {}) == [
            {"n": 0},
        ]
    finally:
        command(f"DROP TABLE plexus_normative.{table} SYNC")
