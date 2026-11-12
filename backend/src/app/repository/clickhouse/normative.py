from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.domain.errors import DataUnavailable
from app.domain.normative.fire import FireProfile, SettlementContext
from app.domain.normative.fire_destination import FireDestination, OriginBasis
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.model import AccessRow, Criterion, Facility, Origin
from app.domain.normative.territory import TerritoryContext
from app.domain.normative.walking_facts import WalkingFacts
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.fire_destinations import FireDestinations
from app.repository.clickhouse.normative_conditions import NormativeConditions
from app.repository.clickhouse.normative_store import NormativeStore
from app.usecase.normative.dto import Assessment, AssessmentReceipt, SavedRun
from app.usecase.normative.route import RouteContext, RouteStage

CRITERIA = """SELECT id,service,act,clause,source_url,edition_date,threshold,unit,mode,
territory,legal_status,verification_status FROM plexus_normative.criteria ORDER BY id"""
FACILITIES = """SELECT id,service,name,address,source_url,observed_at,latitude,longitude,
coordinate_source,coordinate_status,published_on,source_sha256,coordinate_snapshot_sha256,coordinate_snapshot_url FROM plexus_normative.facilities
WHERE service={service:String} ORDER BY id"""
ORIGINS = """SELECT point_id,settlement,population,node,snap_km,lat,lon
FROM plexus_graph.locations WHERE region={region:String} ORDER BY point_id"""


class ClickHouseNormativeRepository:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def latest(self, criterion_id: str) -> SavedRun | None:
        records = self.reader.rows(
            """SELECT id,toUnixTimestamp64Milli(created_at) AS saved_at_ms,criterion_id,act,clause,edition_date,threshold,source_url,graph_revision,
            region,closed_way_ids,model_revision,ignored_way_ids,fire_speed_kmh,fire_assumption,toUnixTimestamp64Milli(qualification_as_of) AS qualification_as_of_ms,origin_basis FROM plexus_normative.runs
            WHERE criterion_id={criterion:String} ORDER BY created_at DESC,id DESC LIMIT 1""",
            {"criterion": criterion_id},
        )
        return self._restore(records[0]) if records else None

    def route_context(self, run_id: str, origin_id: str, stage: RouteStage) -> RouteContext | None:
        records = self.reader.rows(
            """SELECT id,toUnixTimestamp64Milli(created_at) AS saved_at_ms,criterion_id,act,clause,edition_date,threshold,source_url,graph_revision,
            region,closed_way_ids,model_revision,ignored_way_ids,fire_speed_kmh,fire_assumption,toUnixTimestamp64Milli(qualification_as_of) AS qualification_as_of_ms,origin_basis FROM plexus_normative.runs
            WHERE id={id:String} LIMIT 1""",
            {"id": run_id},
        )
        if not records:
            return None
        stored = records[0]
        rows = self.reader.rows(
            """SELECT id,name,population,latitude,longitude,facility_id,minutes,
            excess_minutes,state,distance_metres,uncertainty,routing_node,approach_metres,threshold_minutes,territory_type,territory_source_url,rule_set_id,territory_verification_status,municipality_code,territory_structure_source_url,qualification_source_url,qualification_observed_at,catchment_source_url,threshold_source_url,travel_profile_source_url,measurement_method_source_url,origin_source_url,origin_observed_at,origin_source_sha256,origin_reference_status
            FROM plexus_normative.run_rows WHERE run_id={run:String}
            AND stage={stage:String} AND id={origin:String} LIMIT 1""",
            {"run": run_id, "stage": stage, "origin": origin_id},
        )
        if not rows:
            return None
        row = rows[0]
        row["uncertainty"] = tuple(row["uncertainty"])
        facilities = self.reader.rows(
            """SELECT id,service,name,address,source_url,observed_at,latitude,longitude,
            coordinate_source,coordinate_status,published_on,source_sha256,coordinate_snapshot_sha256,coordinate_snapshot_url FROM plexus_normative.run_facilities
            WHERE run_id={run:String} AND id={facility:String} LIMIT 1""",
            {"run": run_id, "facility": str(row["facility_id"] or "")},
        )
        return RouteContext(
            self._criterion(stored),
            stored["graph_revision"],
            stored["model_revision"],
            AccessRow(**row),
            Facility(**facilities[0]) if facilities else None,
            stored["closed_way_ids"],
            self._fire_profile(stored),
        )

    def _restore(self, stored: dict[str, Any]) -> SavedRun:
        params = {"id": str(stored["id"])}
        criterion = self._criterion(stored)
        facilities = [
            Facility(**r)
            for r in self.reader.rows(
                """SELECT id,service,name,address,
            source_url,observed_at,latitude,longitude,coordinate_source,coordinate_status,published_on,source_sha256,coordinate_snapshot_sha256,coordinate_snapshot_url
            FROM plexus_normative.run_facilities WHERE run_id={id:String} ORDER BY id""",
                params,
            )
        ]
        rows = self.reader.rows(
            """SELECT stage,id,name,population,latitude,longitude,facility_id,
            minutes,excess_minutes,state,distance_metres,uncertainty,routing_node,approach_metres,threshold_minutes,territory_type,territory_source_url,rule_set_id,territory_verification_status,municipality_code,territory_structure_source_url,qualification_source_url,qualification_observed_at,catchment_source_url,threshold_source_url,travel_profile_source_url,measurement_method_source_url,origin_source_url,origin_observed_at,origin_source_sha256,origin_reference_status FROM plexus_normative.run_rows WHERE run_id={id:String}
            ORDER BY stage,id""",
            params,
        )
        baseline: list[AccessRow] = []
        scenario: list[AccessRow] = []
        for row in rows:
            stage = row.pop("stage")
            row["uncertainty"] = tuple(row["uncertainty"])
            entry = AccessRow(**row)
            (baseline if stage == "baseline" else scenario).append(entry)
        return SavedRun(
            criterion,
            facilities,
            stored["graph_revision"],
            stored["region"],
            baseline,
            scenario,
            stored["closed_way_ids"],
            stored["id"],
            stored["model_revision"],
            tuple(stored["ignored_way_ids"]),
            self._fire_profile(stored),
            datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=stored["saved_at_ms"]),
            NormativeConditions(self.reader).rule_sets(str(stored["id"])),
            datetime(1970, 1, 1, tzinfo=UTC)
            + timedelta(milliseconds=stored["qualification_as_of_ms"])
            if stored["qualification_as_of_ms"] is not None
            else None,
            cast(
                OriginBasis,
                stored["origin_basis"]
                or ("residential_references" if criterion.mode == "walk" else "settlements"),
            ),
        )

    def save(self, assessment: Assessment) -> AssessmentReceipt:
        return NormativeStore(self.reader).save(assessment)

    def _fire_profile(self, stored: dict[str, Any]) -> FireProfile | None:
        if stored["fire_speed_kmh"] is None:
            return None
        return FireProfile(stored["fire_speed_kmh"], stored["fire_assumption"] or "")

    def walking_facts(self, service: str) -> list[WalkingFacts]:
        return NormativeConditions(self.reader).facts(service)

    def library_facts(self) -> list[LibraryFacts]:
        return NormativeConditions(self.reader).library_facts()

    def fire_destinations(self, region: str) -> list[FireDestination]:
        return FireDestinations(self.reader).current(region)

    def fire_facts(self) -> list[FireFacts]:
        return NormativeConditions(self.reader).fire_facts()

    def medical_facts(self, service: str) -> list[MedicalFacts]:
        return NormativeConditions(self.reader).medical_facts(service)

    def settlement_types(self) -> list[SettlementContext]:
        return [
            SettlementContext(**row)
            for row in self.reader.rows(
                "SELECT point_id,settlement_type,source_url,verification_status "
                "FROM plexus_normative.settlement_types ORDER BY point_id",
                {},
            )
        ]

    def territories(self) -> list[TerritoryContext]:
        return [
            TerritoryContext(**row)
            for row in self.reader.rows(
                "SELECT point_id,municipality_type,source_url,verification_status,municipality_code,structure_source_url "
                "FROM plexus_normative.territories ORDER BY point_id",
                {},
            )
        ]

    def criteria(self) -> list[Criterion]:
        return [Criterion(**row) for row in self.reader.rows(CRITERIA, {})]

    def facilities(self, service: str) -> list[Facility]:
        return [Facility(**row) for row in self.reader.rows(FACILITIES, {"service": service})]

    def origins(self, region: str) -> list[Origin]:
        return [
            Origin(
                str(r["point_id"]),
                str(r["settlement"]),
                r["population"],
                r["node"],
                r["snap_km"],
                r["lat"],
                r["lon"],
            )
            for r in self.reader.rows(ORIGINS, {"region": region})
        ]

    def walking_origins(self, revision: str) -> list[Origin]:
        rows = self.reader.rows(
            """SELECT id,name,latitude,longitude FROM plexus_normative.pedestrian_origins
            WHERE revision={revision:String} ORDER BY id""",
            {"revision": revision},
        )
        return [
            Origin(row["id"], row["name"], None, None, None, row["latitude"], row["longitude"])
            for row in rows
        ]

    def _criterion(self, stored: dict[str, Any]) -> Criterion:
        params = {"id": str(stored["id"])}
        snapshots = self.reader.rows(
            """SELECT id,service,act,clause,source_url,edition_date,threshold,unit,mode,
            territory,legal_status,verification_status FROM plexus_normative.run_criteria
            WHERE run_id={id:String}""",
            params,
        )
        if snapshots:
            criterion = Criterion(**snapshots[0])
        else:
            current = next((c for c in self.criteria() if c.id == stored["criterion_id"]), None)
            if current is None:
                raise DataUnavailable("The stored criterion is incomplete")
            criterion = replace(
                current,
                act=stored["act"],
                clause=stored["clause"],
                edition_date=stored["edition_date"],
                threshold=stored["threshold"],
                source_url=stored["source_url"],
            )
        return criterion
