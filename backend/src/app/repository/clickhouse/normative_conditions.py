from dataclasses import fields

from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.rules import RuleCheck, RuleSet
from app.domain.normative.walking_facts import WalkingFacts
from app.repository.clickhouse.client import ClickHouseReader


class NormativeConditions:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def library_facts(self) -> list[LibraryFacts]:
        columns = ",".join(field.name for field in fields(LibraryFacts))
        records = self.reader.rows(
            f"SELECT {columns} FROM plexus_normative.library_facts ORDER BY origin_id", {}
        )
        for row in records:
            row["eligible_facility_ids"] = tuple(row["eligible_facility_ids"])
            row["verified_closed_way_ids"] = tuple(row["verified_closed_way_ids"])
        return [LibraryFacts(**row) for row in records]

    def fire_facts(self) -> list[FireFacts]:
        columns = ",".join(field.name for field in fields(FireFacts))
        records = self.reader.rows(
            f"SELECT {columns} FROM plexus_normative.fire_facts ORDER BY origin_id", {}
        )
        for row in records:
            row["eligible_facility_ids"] = tuple(row["eligible_facility_ids"])
            row["verified_closed_way_ids"] = tuple(row["verified_closed_way_ids"])
        return [FireFacts(**row) for row in records]

    def medical_facts(self, service: str) -> list[MedicalFacts]:
        columns = ",".join(field.name for field in fields(MedicalFacts))
        records = self.reader.rows(
            f"SELECT {columns} FROM plexus_normative.medical_facts WHERE service={{service:String}} ORDER BY origin_id",
            {"service": service},
        )
        for row in records:
            row["eligible_facility_ids"] = tuple(row["eligible_facility_ids"])
            row["verified_closed_way_ids"] = tuple(row["verified_closed_way_ids"])
        return [MedicalFacts(**row) for row in records]

    def facts(self, service: str) -> list[WalkingFacts]:
        columns = ",".join(field.name for field in fields(WalkingFacts))
        records = self.reader.rows(
            f"SELECT {columns} FROM plexus_normative.walking_facts "
            "WHERE service={service:String} ORDER BY origin_id",
            {"service": service},
        )
        for row in records:
            row["zones"] = tuple(row["zones"])
            row["eligible_facility_ids"] = tuple(row["eligible_facility_ids"])
            row["verified_closed_way_ids"] = tuple(row["verified_closed_way_ids"])
        return [WalkingFacts(**row) for row in records]

    def rule_sets(self, run_id: str) -> tuple[RuleSet, ...]:
        records = self.reader.rows(
            "SELECT id,checks FROM plexus_normative.run_rule_sets WHERE run_id={id:String} "
            "ORDER BY id SETTINGS output_format_json_named_tuples_as_objects=1",
            {"id": run_id},
        )
        result = []
        for row in records:
            for check in row["checks"]:
                check["candidate_thresholds"] = tuple(check["candidate_thresholds"])
            result.append(RuleSet(row["id"], tuple(RuleCheck(**check) for check in row["checks"])))
        return tuple(result)
