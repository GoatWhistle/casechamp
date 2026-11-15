import json
from dataclasses import replace
from uuid import uuid4

from analytics.client import ClickHouse
from analytics.migrate_road_capacity import fingerprint, migrate
from app.domain.appraisal import appraise
from app.domain.appraisal_inputs import (
    DemandScenario,
    FreightFlow,
    FreightTravelChange,
    PassengerFlow,
    ProjectAssumptions,
    TravelChange,
)
from app.repository.clickhouse.capacity_state import restore_capacity_defaults
from app.repository.clickhouse.records import columns, decode, encode
from app.usecase.road_graph import RoadChange, RoadJob, RoadResult, SettlementEffect


def fixture_job() -> RoadJob:
    project = ProjectAssumptions(
        [PassengerFlow("point", "market", 1234.5, 321.0, "источник", origin_name="пункт")],
        [
            DemandScenario("low", 0.5, 0.8),
            DemandScenario("base", 1.0, 1.0),
            DemandScenario("high", 1.5, 1.2),
        ],
        123456.0,
        789.0,
        12,
        0.05,
        2025,
        "costs",
        [FreightFlow("manual", 456.0, 4.5, 3.5, 100.5, 90.5, 1000.0, 20.0, "manual source")],
    )
    return RoadJob(
        "legacy",
        "32000000",
        "Кемеровская область",
        "road",
        [RoadChange(123, 1.25)],
        "completed",
        3,
        3,
        "legacy-fixture",
        RoadResult(
            95.5,
            97.25,
            1.75,
            1.8,
            100,
            3,
            2,
            54321.5,
            0.125,
            settlement_effects=[SettlementEffect("point", 95.5, 97.25, 1.75)],
        ),
        appraisal_assumptions=project,
        appraisal_result=appraise(project, [TravelChange("point", "market", 4.5, 3.5)]),
    )


def insert_job(client: ClickHouse, table: str, job: RoadJob, *, legacy: bool = False) -> None:
    value = encode(RoadJob, job)
    if legacy:
        value["changes"] = [
            {"way_id": r["way_id"], "speed_factor": r["speed_factor"]} for r in value["changes"]
        ]
        for result in value["result"]:
            result.pop("road_cost_method", None)
            result.pop("road_cost_notes", None)
        for project in value["appraisal_assumptions"]:
            for freight in project["freight"]:
                freight.pop("origin_point_id", None)
                freight.pop("market_city", None)
        for result in value["appraisal_result"]:
            for field in ["freight_travel", "unresolved_freight_flows", "freight_routing_scope"]:
                result.pop(field, None)
    client.request(
        f"INSERT INTO {table} FORMAT JSONEachRow",
        json.dumps(value, ensure_ascii=False).encode(),
    )


def test_persisted_road_job_migration_preserves_legacy_and_accepts_new_profiles() -> None:
    client = ClickHouse()
    database = "traffic_migration_test_" + uuid4().hex[:12]
    table = database + ".road_jobs"
    try:
        client.request("CREATE DATABASE " + database)
        legacy_backup = "plexus_state.road_jobs_before_capacity_v1"
        schema_source = (
            legacy_backup
            if client.rows("EXISTS TABLE " + legacy_backup)[0]["result"]
            else "plexus_state.road_jobs"
        )
        client.request(f"CREATE TABLE {table} AS {schema_source}")
        types = {
            row["name"]: row["type"]
            for row in client.rows("DESCRIBE TABLE " + table)
            if row["name"] in {"changes", "result", "appraisal_assumptions", "appraisal_result"}
        }
        legacy = fixture_job()
        assert legacy.appraisal_assumptions is not None
        assert legacy.result is not None
        insert_job(client, table, legacy, legacy=True)
        before = fingerprint(client, table, types)
        report = migrate(client, database)
        after = fingerprint(client, table, types)
        assert before == after
        assert report["status"] in {"migrated", "already_current"}
        if report["status"] == "migrated":
            assert fingerprint(client, report["backup"], types) == before
        stored = client.rows(f"SELECT {columns(RoadJob)} FROM {table} FINAL WHERE id='legacy'")[0]
        restored = decode(RoadJob, restore_capacity_defaults(stored))
        assert restored == legacy
        assert restored.changes[0].lanes_total is None
        assert restored.result.road_cost_method == "legacy_speed_v1"
        assert restored.appraisal_assumptions.freight[0].origin_point_id == ""
        assert restored.appraisal_assumptions.freight[0].market_city == ""
        assert restored.appraisal_result.freight_travel == []
        assert restored.appraisal_result.freight_routing_scope == "manual_supplied_travel"
        project = replace(
            legacy.appraisal_assumptions,
            freight=[
                FreightFlow(
                    "routed",
                    456.0,
                    None,
                    None,
                    None,
                    None,
                    1000.0,
                    20.0,
                    "routing source",
                    origin_point_id="point",
                    market_city="market",
                )
            ],
        )
        current = replace(
            legacy,
            id="new",
            changes=[RoadChange(123, 1.0, 4, "motorway", "asphalt", 100.0)],
            result=replace(
                legacy.result, road_cost_method="road-capacity-v1", road_cost_notes=["unknown flow"]
            ),
            appraisal_assumptions=project,
            appraisal_result=appraise(
                project,
                [TravelChange("point", "market", 4.5, 3.5)],
                [FreightTravelChange("routed", 4.5, 3.5, 100.5, 90.5)],
            ),
        )
        insert_job(client, table, current)
        row = client.rows(f"SELECT {columns(RoadJob)} FROM {table} FINAL WHERE id='new'")[0]
        assert decode(RoadJob, restore_capacity_defaults(row)) == current
        assert migrate(client, database)["status"] == "already_current"
    finally:
        client.request("DROP DATABASE IF EXISTS " + database)
