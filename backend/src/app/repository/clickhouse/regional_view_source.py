from collections import OrderedDict
from dataclasses import fields
from threading import Lock
from typing import Any

from app.domain.errors import DataUnavailable
from app.domain.normative.comparison import RouteComparison
from app.domain.normative.fire import FireProfile
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow, Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.usecase.normative.regional_view import RegionalRunView


class RegionalViewSource:
    def __init__(self, reader: ClickHouseReader, table: str) -> None:
        self.reader = reader
        self.table = table
        self.repository = ClickHouseRegionalMeasurementRepository(reader)
        self.repository.table = table
        self.lock = Lock()
        self.metadata: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.legacy: tuple[str, dict[str, Any]] | None = None

    def latest_id(self, region_id: str, criterion_id: str) -> str | None:
        rows = self.reader.rows(
            f"SELECT id FROM {self.table} WHERE region_id={{region:String}} "
            "AND criterion_id={criterion:String} ORDER BY saved_at DESC,id DESC LIMIT 1",
            {"region": region_id, "criterion": criterion_id},
        )
        return str(rows[0]["id"]) if rows else None

    def load(self, run_id: str) -> dict[str, Any] | None:
        with self.lock:
            if run_id in self.metadata:
                self.metadata.move_to_end(run_id)
                return self.metadata[run_id]
            record = self.fetch(run_id)
            if record is None:
                return None
            storage = record.get("snapshot_storage", "legacy_json")
            if storage not in {"legacy_json", "regional_arrow_v1"}:
                raise DataUnavailable("The regional snapshot format is unsupported")
            if storage == "legacy_json":
                self.legacy = (run_id, record)
                counts = {
                    "baseline": len(record["baseline_rows"]),
                    "scenario": len(record["rows"]),
                    "facilities": len(record["facilities"]),
                }
            else:
                counts = record["snapshot_counts"]
                self.validate_counts(run_id, counts)
            meta = {
                key: value
                for key, value in record.items()
                if key not in {"rows", "baseline_rows", "facilities"}
            }
            meta["snapshot_storage"] = storage
            meta["snapshot_counts"] = counts
            self.metadata[run_id] = meta
            if len(self.metadata) > 64:
                self.metadata.popitem(last=False)
            return meta

    def validate_counts(self, run_id: str, expected: dict[str, int]) -> None:
        rows = self.reader.rows(
            f"SELECT stage,count() AS n,uniqExact(position) AS distinct_positions,min(position) AS first,max(position) AS last FROM {self.table}_rows WHERE run_id={{run:String}} GROUP BY stage",
            {"run": run_id},
        )
        found = {row["stage"]: row for row in rows}
        for stage in ("baseline", "scenario"):
            row = found.get(stage)
            count = expected[stage]
            if count and (
                row is None
                or row["n"] != count
                or row["distinct_positions"] != count
                or row["first"] != 0
                or row["last"] != count - 1
            ):
                raise DataUnavailable("The regional row snapshot is incomplete")
            if not count and row is not None:
                raise DataUnavailable("The regional row snapshot has unexpected records")
        facilities = self.reader.rows(
            f"SELECT count() AS n,uniqExact(position) AS distinct_positions FROM {self.table}_facilities WHERE run_id={{run:String}}",
            {"run": run_id},
        )[0]
        if (
            facilities["n"] != expected["facilities"]
            or facilities["distinct_positions"] != expected["facilities"]
        ):
            raise DataUnavailable("The regional facility snapshot is incomplete")

    def fetch(self, run_id: str) -> dict[str, Any] | None:
        return self.repository.record(
            f"SELECT payload FROM {self.table} WHERE id={{id:String}} LIMIT 1", {"id": run_id}
        )

    def legacy_record(self, run_id: str) -> dict[str, Any]:
        with self.lock:
            if self.legacy is None or self.legacy[0] != run_id:
                self.legacy = None
                record = self.fetch(run_id)
                if record is None:
                    raise DataUnavailable("The saved regional snapshot is unavailable")
                self.legacy = (run_id, record)
            return self.legacy[1]

    def normalized(self, run_id: str) -> bool:
        metadata = self.load(run_id)
        if metadata is None:
            raise DataUnavailable("The saved regional snapshot is unavailable")
        return bool(metadata["snapshot_storage"] == "regional_arrow_v1")

    def view(self, run_id: str) -> RegionalRunView | None:
        metadata = self.load(run_id)
        if metadata is None:
            return None
        counts = metadata["snapshot_counts"]
        comparison = RouteComparison(**metadata["comparison"])
        common = {
            field.name: metadata[field.name]
            for field in fields(RegionalRunView)
            if field.name in metadata
            and field.name
            not in {
                "comparison",
                "fire_profile",
                "origins",
                "baseline_measured_paths",
                "scenario_measured_paths",
                "facility_count",
            }
        }
        for key, default in (
            ("mode", "car"),
            ("unit", "minutes"),
            ("qualification", "physical_only"),
            ("model_revision", "regional-road-v1"),
            ("measurement_definition", MeasurementDefinition.SINGLE_REFERENCE_POINT),
        ):
            common.setdefault(key, default)
        return RegionalRunView(
            **common,
            comparison=comparison,
            fire_profile=FireProfile(**metadata["fire_profile"])
            if metadata.get("fire_profile")
            else None,
            origins=counts["scenario"],
            baseline_measured_paths=comparison.paired_paths + comparison.lost,
            scenario_measured_paths=comparison.paired_paths + comparison.restored,
            facility_count=counts["facilities"],
        )


def access_row(record: dict[str, Any]) -> AccessRow:
    return AccessRow(**{**record, "uncertainty": tuple(record.get("uncertainty", ()))})


def facility(record: dict[str, Any]) -> Facility:
    return Facility(**record)
