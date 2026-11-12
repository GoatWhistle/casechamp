import json
from dataclasses import replace

from app.domain.normative.index import IndexValue
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.scenario_index import ScenarioIndex, ScenarioIndexPolicy, scenario_policy
from app.repository.clickhouse.client import ClickHouseReader


class ClickHouseScenarioIndexRepository:
    table = "plexus_normative.scenario_index_summaries"
    measurement_table = "plexus_normative.regional_measurements"

    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def latest(self, region_id: str, criterion_id: str) -> ScenarioIndex | None:
        return next((r for r in self.regions(criterion_id) if r.region_id == region_id), None)

    def regions(self, criterion_id: str) -> list[ScenarioIndex]:
        policy = scenario_policy(criterion_id)
        rows = self.reader.rows(
            f"SELECT s.payload,h.run_id AS head_run_id,h.measurement_definition AS head_definition,s.region_id AS head_region FROM {self.table} AS s FINAL "
            f"INNER JOIN (SELECT region_id,argMax(id,tuple(saved_at,id)) AS run_id,"
            "argMax(measurement_definition,tuple(saved_at,id)) AS measurement_definition "
            f"FROM {self.measurement_table} WHERE criterion_id={{criterion:String}} "
            "GROUP BY region_id) AS h ON s.region_id=h.region_id AND s.run_id=h.run_id "
            "WHERE s.criterion_id={criterion:String} AND s.policy_sha256={policy:String}",
            {"criterion": criterion_id, "policy": policy.definition_sha256},
        )
        result = []
        for row in rows:
            record = json.loads(row["payload"])
            definition = MeasurementDefinition(record["measurement_definition"])
            saved_policy = record.pop("policy")
            restored_policy = ScenarioIndexPolicy(
                **{**saved_policy, "thresholds": tuple(saved_policy["thresholds"])}
            )
            if (
                restored_policy != policy
                or record["run_id"] != row["head_run_id"]
                or record["criterion_id"] != criterion_id
                or record["region_id"] != row["head_region"]
                or definition != row["head_definition"]
                or definition != MeasurementDefinition.SINGLE_REFERENCE_POINT
                or record.get("legal_compliance_confirmed") is not False
            ):
                continue
            for stage in ("baseline", "scenario"):
                record[stage] = [IndexValue(**value) for value in record[stage]]
            result.append(
                replace(ScenarioIndex(policy=policy, **record), measurement_definition=definition)
            )
        return result
