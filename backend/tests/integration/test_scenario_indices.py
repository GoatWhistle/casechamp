import json
from dataclasses import asdict
from urllib.request import Request, urlopen
from uuid import uuid4

from tests.storage import settings
from tests.unit.usecase.test_scenario_indices import model

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.scenario_indices import ClickHouseScenarioIndexRepository


def test_scenario_cache_expires_with_measurement_head_without_reading_measurement_payload() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password, max_threads=1
    )
    prefix = "plexus_normative.test_scenario_" + uuid4().hex
    repository = ClickHouseScenarioIndexRepository(reader)
    repository.table = prefix
    repository.measurement_table = prefix + "_measurements"

    def command(sql: str) -> None:
        with urlopen(
            Request(reader.url + "/", data=sql.encode(), headers=reader.headers), timeout=60
        ) as response:
            response.read()

    command(f"CREATE TABLE {prefix} AS plexus_normative.scenario_index_summaries")
    command(
        f"CREATE TABLE {repository.measurement_table} AS plexus_normative.regional_measurements"
    )
    try:
        value = model()
        command(
            f"INSERT INTO {prefix} FORMAT JSONEachRow\n"
            + json.dumps(
                {
                    "region_id": value.region_id,
                    "criterion_id": value.criterion_id,
                    "run_id": value.run_id,
                    "policy_sha256": value.policy.definition_sha256,
                    "payload": json.dumps(asdict(value)),
                    "publication_version": 1,
                }
            )
        )
        head = {
            "id": value.run_id,
            "region_id": "R",
            "criterion_id": "N06",
            "saved_at": "2026-11-12T01:00:00",
            "payload": "invalid legacy payload intentionally unused",
            "measurement_definition": "single_reference_point",
        }
        command(
            f"INSERT INTO {repository.measurement_table} FORMAT JSONEachRow\n" + json.dumps(head)
        )
        assert repository.latest("R", "N06") == value
        assert repository.latest("Other", "N06") is None
        command(
            f"INSERT INTO {repository.measurement_table} FORMAT JSONEachRow\n"
            + json.dumps({**head, "id": "new", "saved_at": "2026-11-12T02:00:00"})
        )
        assert repository.latest("R", "N06") is None
        assert repository.regions("N06") == []
    finally:
        command(f"DROP TABLE {prefix}")
        command(f"DROP TABLE {repository.measurement_table}")
