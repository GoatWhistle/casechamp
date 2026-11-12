import json
from dataclasses import asdict, fields
from typing import Any
from urllib.request import Request, urlopen

import pyarrow as pa
from pyarrow import ipc

from app.domain.errors import DataUnavailable
from app.domain.normative.comparison import RouteComparison
from app.domain.normative.fire import FireProfile
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow, Facility, Origin
from app.repository.clickhouse.client import ClickHouseReader, QueryValue
from app.repository.clickhouse.normative import ClickHouseNormativeRepository
from app.repository.clickhouse.regional_measurement_head import latest_measurement_head
from app.repository.clickhouse.regional_snapshots import RegionalSnapshots
from app.usecase.normative.regional_measurements import RegionalMeasurement
from app.usecase.normative.regional_receipt import (
    RegionalMeasurementHead,
    RegionalMeasurementReceipt,
)


class ClickHouseRegionalMeasurementRepository:
    table = "plexus_normative.regional_measurements"

    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def origins(self, region_id: str) -> list[Origin]:
        rows = self.reader.rows(
            "SELECT id,name,population,node,snap_km,latitude,longitude "
            "FROM plexus_normative.regional_origin_points FINAL "
            "WHERE region_id={region:String} AND snapshot=("
            "SELECT revision FROM plexus_normative.regional_origin_snapshots "
            "WHERE graph_revision=(SELECT value FROM plexus_atlas.atlas_metadata "
            "WHERE key='graph_revision') ORDER BY created_at DESC LIMIT 1) ORDER BY id",
            {"region": region_id},
        )
        return [Origin(**row) for row in rows]

    def walking_origins(self, revision: str) -> list[Origin]:
        return ClickHouseNormativeRepository(self.reader).walking_origins(revision)

    def save(self, result: RegionalMeasurement) -> None:
        snapshots = RegionalSnapshots(self.reader, self.table)
        snapshots.save_rows(result.run_id, "baseline", result.baseline_rows)
        snapshots.save_rows(result.run_id, "scenario", result.rows)
        snapshots.save_facilities(result.run_id, result.facilities)
        metadata = {
            field.name: getattr(result, field.name)
            for field in fields(result)
            if field.name
            not in {"baseline_rows", "rows", "facilities", "comparison", "fire_profile"}
        }
        metadata["comparison"] = asdict(result.comparison)
        metadata["fire_profile"] = asdict(result.fire_profile) if result.fire_profile else None
        metadata["snapshot_storage"] = "regional_arrow_v1"
        metadata["snapshot_counts"] = {
            "baseline": len(result.baseline_rows),
            "scenario": len(result.rows),
            "facilities": len(result.facilities),
        }
        record = {
            "id": result.run_id,
            "region_id": result.region_id,
            "criterion_id": result.criterion_id,
            "saved_at": result.saved_at,
            "measurement_definition": result.measurement_definition,
            "payload": json.dumps(metadata, ensure_ascii=False, allow_nan=False),
        }
        schema = pa.schema([(key, pa.string()) for key in record])
        sink = pa.BufferOutputStream()
        with ipc.new_stream(sink, schema) as writer:
            writer.write_table(pa.Table.from_pylist([record], schema=schema))
        sql = (
            f"INSERT INTO {self.table} "
            "SETTINGS max_threads=1,max_insert_threads=1 FORMAT ArrowStream\n"
        )
        request = Request(
            self.reader.url + "/",
            data=sql.encode() + sink.getvalue().to_pybytes(),
            headers={k: v for k, v in self.reader.headers.items() if k != "Accept-Encoding"},
        )
        try:
            with urlopen(request, timeout=60) as response:
                response.read()
        except OSError as error:
            raise DataUnavailable("Regional measurement storage is unavailable") from error

    def latest(self, region_id: str, criterion_id: str) -> RegionalMeasurement | None:
        record = self.record(
            f"SELECT payload FROM {self.table} "
            "WHERE region_id={region:String} AND criterion_id={criterion:String} "
            "ORDER BY saved_at DESC,id DESC LIMIT 1",
            {"region": region_id, "criterion": criterion_id},
        )
        return self.restore(record) if record else None

    def latest_head(self, region_id: str, criterion_id: str) -> RegionalMeasurementHead | None:
        return latest_measurement_head(self.reader, self.table, region_id, criterion_id)

    def latest_receipt(
        self, region_id: str, criterion_id: str
    ) -> RegionalMeasurementReceipt | None:
        record = self.record(
            f"SELECT payload FROM {self.table} "
            "WHERE region_id={region:String} AND criterion_id={criterion:String} "
            "ORDER BY saved_at DESC,id DESC LIMIT 1",
            {"region": region_id, "criterion": criterion_id},
        )
        if record is None:
            return None
        counts = record.get("snapshot_counts")
        if counts is None:
            counts = {"scenario": len(record["rows"]), "facilities": len(record["facilities"])}
        for key, default in (
            ("mode", "car"),
            ("unit", "minutes"),
            ("qualification", "physical_only"),
            ("model_revision", "regional-road-v1"),
            ("measurement_definition", MeasurementDefinition.SINGLE_REFERENCE_POINT),
        ):
            record.setdefault(key, default)
        common = {
            field.name: record[field.name]
            for field in fields(RegionalMeasurementReceipt)
            if field.name not in {"origins", "measured_paths", "facilities"}
        }
        return RegionalMeasurementReceipt(
            **common,
            origins=counts["scenario"],
            facilities=counts["facilities"],
            measured_paths=record["comparison"]["paired_paths"] + record["comparison"]["restored"],
        )

    def get(self, run_id: str) -> RegionalMeasurement | None:
        record = self.record(
            f"SELECT payload FROM {self.table} WHERE id={{id:String}} LIMIT 1",
            {"id": run_id},
        )
        return self.restore(record) if record else None

    def record(self, sql: str, params: dict[str, QueryValue]) -> dict[str, Any] | None:
        with self.reader.response(sql, params, "RawBLOB") as response:
            payload = response.read()
        record: dict[str, Any] | None = json.loads(payload) if payload else None
        return record

    def restore(self, record: dict[str, Any]) -> RegionalMeasurement:
        storage = record.pop("snapshot_storage", None)
        if storage is not None:
            if storage != "regional_arrow_v1":
                raise DataUnavailable("The regional snapshot format is unsupported")
            counts = record.pop("snapshot_counts")
            snapshots = RegionalSnapshots(self.reader, self.table)
            record["baseline_rows"] = snapshots.load(
                record["run_id"], "rows", counts["baseline"], "baseline"
            )
            record["rows"] = snapshots.load(
                record["run_id"], "rows", counts["scenario"], "scenario"
            )
            record["facilities"] = snapshots.load(
                record["run_id"], "facilities", counts["facilities"]
            )
        return restore_record(record)


def restore_record(record: dict[str, Any]) -> RegionalMeasurement:
    record["measurement_definition"] = MeasurementDefinition(
        record.get("measurement_definition", MeasurementDefinition.SINGLE_REFERENCE_POINT)
    )
    record["facilities"] = [Facility(**row) for row in record["facilities"]]
    for stage in ("baseline_rows", "rows"):
        record[stage] = [
            AccessRow(**{**row, "uncertainty": tuple(row["uncertainty"])}) for row in record[stage]
        ]
    record["comparison"] = RouteComparison(**record["comparison"])
    if record.get("fire_profile") is not None:
        record["fire_profile"] = FireProfile(**record["fire_profile"])
    return RegionalMeasurement(**record)
