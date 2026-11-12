import json
from dataclasses import asdict, replace
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.errors import DataUnavailable
from app.domain.normative.comparison import compare_routes
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.repository.clickhouse.regional_view import ClickHouseRegionalViewRepository
from app.usecase.normative.regional_measurements import RegionalMeasurement


def test_regional_snapshot_preserves_sources_geometry_and_scope_in_real_storage() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    table = "plexus_normative.test_regional_" + uuid4().hex

    def command(sql: str) -> None:
        request = Request(reader.url + "/", data=sql.encode(), headers=reader.headers)
        with urlopen(request, timeout=60) as response:
            response.read()

    repository = ClickHouseRegionalMeasurementRepository(reader)
    repository.table = table
    command(f"CREATE TABLE {table} AS plexus_normative.regional_measurements")
    for kind in ("rows", "facilities"):
        command(f"CREATE TABLE {table}_{kind} AS plexus_normative.regional_measurements_{kind}")
    try:
        target = replace(
            facility(),
            source_sha256="a" * 64,
            coordinate_source="https://example.org/point",
            latitude=55,
            longitude=65,
            coordinate_snapshot_sha256="b" * 64,
            coordinate_snapshot_url="https://example.org/snapshot",
        )
        rows = [
            AccessRow(
                "p",
                "Place",
                None,
                55,
                65,
                target.id,
                3.12345678912345,
                None,
                "unknown",
                uncertainty=("facility_profile_unconfirmed",),
                routing_node=2,
                approach_metres=1.234567891,
            )
        ]
        rows = [replace(rows[0], id=f"p{1002 - i:04}") for i in range(10003)]
        result = RegionalMeasurement(
            uuid4().hex,
            "A",
            "Region A",
            "N01",
            "medical",
            "graph-test",
            "2026-11-12T10:00:00+00:00",
            [target],
            rows,
            rows,
            [],
            compare_routes(rows, rows, "minutes"),
        )
        repository.save(result)
        assert repository.latest_receipt("A", "N01") == result.receipt()
        assert repository.get(result.run_id) == result
        assert repository.latest("A", "N01") == result
        assert repository.latest("B", "N01") is None
        assert (
            reader.rows(
                f"SELECT measurement_definition FROM {table} WHERE id={{run:String}}",
                {"run": result.run_id},
            )[0]["measurement_definition"]
            == "single_reference_point"
        )
        other = replace(
            result,
            run_id=uuid4().hex,
            region_id="B",
            region_name="Region B",
            saved_at="2026-11-12T11:00:00+00:00",
        )
        repository.save(other)
        assert repository.latest("A", "N01") == result
        assert repository.latest("B", "N01") == other
        restored = repository.get(result.run_id)
        assert restored is not None
        assert restored.facilities[0].coordinate_snapshot_sha256 == "b" * 64
        parcel_rows = [replace(row, minutes=None, distance_metres=400) for row in rows[:3]]
        parcel = replace(
            result,
            run_id=uuid4().hex,
            region_id="Parcel",
            criterion_id="N09",
            mode="walk",
            unit="metres",
            model_revision="test-parcel-model",
            measurement_definition=MeasurementDefinition.STOP_PAVILION_PARCEL_BOUNDARY,
            baseline_rows=parcel_rows,
            rows=parcel_rows,
            comparison=compare_routes(parcel_rows, parcel_rows, "metres"),
        )
        repository.save(parcel)
        assert repository.get(parcel.run_id) == parcel
        assert repository.latest_receipt("Parcel", "N09") == parcel.receipt()
        view = ClickHouseRegionalViewRepository(reader, table).view(parcel.run_id)
        assert view is not None and view.measurement_definition == parcel.measurement_definition
        assert (
            reader.rows(
                f"SELECT measurement_definition FROM {table} WHERE id={{run:String}}",
                {"run": parcel.run_id},
            )[0]["measurement_definition"]
            == parcel.measurement_definition
        )
        legacy_rows = rows[:3]
        legacy = replace(
            result,
            run_id=uuid4().hex,
            region_id="Legacy",
            baseline_rows=legacy_rows,
            rows=legacy_rows,
            comparison=compare_routes(legacy_rows, legacy_rows, "minutes"),
        )
        payload = asdict(legacy)
        for key in ("mode", "unit", "qualification", "model_revision", "measurement_definition"):
            payload.pop(key)
        command(
            f"INSERT INTO {table} FORMAT JSONEachRow\n"
            + json.dumps(
                {
                    "id": legacy.run_id,
                    "region_id": "Legacy",
                    "criterion_id": "N01",
                    "saved_at": legacy.saved_at,
                    "payload": json.dumps(payload),
                }
            )
        )
        assert repository.latest_receipt("Legacy", "N01") == legacy.receipt()
        assert repository.get(legacy.run_id) == legacy

        command(
            f"ALTER TABLE {table}_rows DELETE WHERE run_id='{result.run_id}' AND stage='scenario' AND position=9000 SETTINGS mutations_sync=1"
        )
        with pytest.raises(DataUnavailable):
            repository.get(result.run_id)
    finally:
        command(f"DROP TABLE {table}")
        command(f"DROP TABLE {table}_rows")
        command(f"DROP TABLE {table}_facilities")
