import json
from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock
from urllib.request import Request, urlopen
from uuid import uuid4

from tests.storage import settings
from tests.unit.usecase.test_regional_index_modes import evaluate

from app.domain.normative.index import IndexBasisReview
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.index_map import ClickHouseIndexMapRepository
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.usecase.normative.index_map import IndexMapQueries
from app.usecase.normative.indices import IndexBasisRepository, RegionalIndices


def test_cached_index_matches_the_saved_result_and_rejects_new_runs_and_changed_law() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    repository = ClickHouseIndexMapRepository(reader)
    suffix = uuid4().hex
    repository.summary_table = "plexus_normative.test_index_cache_" + suffix
    repository.measurement_table = "plexus_normative.test_index_heads_" + suffix

    def command(sql: str) -> None:
        request = Request(reader.url + "/", data=sql.encode(), headers=reader.headers)
        with urlopen(request, timeout=60) as response:
            response.read()

    command(f"CREATE TABLE {repository.summary_table} AS plexus_normative.index_summaries")
    command(
        f"CREATE TABLE {repository.measurement_table} AS plexus_normative.regional_measurements"
    )
    try:
        index = evaluate("walk")
        assert index.basis is not None
        index = replace(
            index,
            basis=replace(
                index.basis,
                review=IndexBasisReview(
                    "2026-11-12",
                    "2026-10-22",
                    "sheet1!A226:J226",
                    "https://example.org/registry.xlsx",
                    "a" * 64,
                    "registry_listing",
                ),
            ),
        )
        assert index.basis is not None
        record = {
            "id": index.run_id,
            "region_id": "R",
            "criterion_id": "N04",
            "saved_at": "2026-11-12T12:00:00",
            "payload": "",
        }
        command(
            f"INSERT INTO {repository.measurement_table} FORMAT JSONEachRow\n" + json.dumps(record)
        )
        queries = IndexMapQueries(repository, lambda: datetime.now(UTC))
        assert queries.publish(index)
        assert repository.latest("R", "N04", index.basis) == index
        bases = Mock(spec=IndexBasisRepository)
        bases.region_exists.return_value = True
        bases.basis.return_value = replace(
            index.basis,
            required_measurement_definition=MeasurementDefinition.STOP_PAVILION_PARCEL_BOUNDARY,
        )
        measurements = ClickHouseRegionalMeasurementRepository(reader)
        measurements.table = repository.measurement_table
        guarded = RegionalIndices(cast(IndexBasisRepository, bases), measurements).latest(
            "R", "N04"
        )
        assert guarded.status == "measurement_incompatible" and guarded.scenario == []
        assert guarded.run_id == index.run_id
        assert (
            repository.latest(
                "R",
                "N04",
                replace(
                    index.basis,
                    required_measurement_definition=MeasurementDefinition.STOP_PAVILION_PARCEL_BOUNDARY,
                ),
            )
            is None
        )
        assert (
            repository.latest("R", "N04", replace(index.basis, definition_sha256="b" * 64)) is None
        )
        record.update(id="new-run", saved_at="2026-11-12T13:00:00")
        command(
            f"INSERT INTO {repository.measurement_table} FORMAT JSONEachRow\n" + json.dumps(record)
        )
        assert repository.latest("R", "N04", index.basis) is None
        newer = replace(index, run_id="new-run")
        assert queries.publish(newer)
        assert repository.latest("R", "N04", index.basis) == newer
    finally:
        command(f"DROP TABLE {repository.summary_table}")
        command(f"DROP TABLE {repository.measurement_table}")
