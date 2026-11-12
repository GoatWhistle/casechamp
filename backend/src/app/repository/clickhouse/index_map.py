import json
from dataclasses import asdict
from typing import Any
from urllib.request import Request, urlopen

from app.domain.errors import DataUnavailable
from app.domain.normative.index import IndexBasis, IndexValue
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.index_basis_record import basis_from_record
from app.repository.clickhouse.regional_measurement_head import latest_measurement_head
from app.usecase.normative.index_map import IndexMapInput, IndexSummary
from app.usecase.normative.indices import RegionalIndex


class ClickHouseIndexMapRepository:
    summary_table = "plexus_normative.index_summaries"
    measurement_table = "plexus_normative.regional_measurements"

    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def inputs(self, criterion_id: str) -> list[IndexMapInput]:
        params = {"criterion": criterion_id}
        regions = self.reader.rows(
            "SELECT id,name FROM plexus_normative.inventory_regions FINAL ORDER BY id", {}
        )
        latest = self.reader.rows(
            "SELECT region_id,argMax(id,tuple(saved_at,id)) AS run_id,argMax(measurement_definition,tuple(saved_at,id)) AS measurement_definition FROM plexus_normative.regional_measurements WHERE criterion_id={criterion:String} GROUP BY region_id",
            params,
        )
        summaries = self.reader.rows(
            "SELECT region_id,criterion_id,run_id,measured_at,definition_sha256,unit,weighting,threshold_min,threshold_max,baseline_min,baseline_max,scenario_min,scenario_max,reference_points,measured_points,publication_version,index_payload FROM plexus_normative.index_summaries FINAL WHERE criterion_id={criterion:String}",
            params,
        )
        bases = self.reader.rows(
            "SELECT criterion_id,region_id,act,clause,edition_date,source_url,unit,thresholds,definition_sha256,currentness,required_mode,regulation,review,intervals,required_measurement_definition FROM plexus_normative.index_bases FINAL WHERE criterion_id={criterion:String}",
            params,
        )
        by_run = {str(row["region_id"]): str(row["run_id"]) for row in latest}
        definitions = {
            row["region_id"]: MeasurementDefinition(row["measurement_definition"]) for row in latest
        }
        by_summary = {str(row["region_id"]): restore_summary(row) for row in summaries}
        by_basis = {str(row["region_id"]): basis_from_record(row) for row in bases}
        return [
            IndexMapInput(
                row["id"],
                row["name"],
                by_basis.get(row["id"], by_basis.get("RU")),
                by_run.get(row["id"]),
                by_summary.get(row["id"]),
                definitions.get(row["id"], MeasurementDefinition.SINGLE_REFERENCE_POINT),
            )
            for row in regions
        ]

    def latest(self, region_id: str, criterion_id: str, basis: IndexBasis) -> RegionalIndex | None:
        params = {"region": region_id, "criterion": criterion_id}
        head = latest_measurement_head(self.reader, self.measurement_table, region_id, criterion_id)
        if head is None:
            return None
        rows = self.reader.rows(
            f"SELECT index_payload FROM {self.summary_table} FINAL "
            "WHERE region_id={region:String} AND criterion_id={criterion:String} "
            "AND run_id={run:String} AND definition_sha256={definition:String}",
            {**params, "run": head.run_id, "definition": basis.definition_sha256},
        )
        if not rows or not rows[0]["index_payload"]:
            return None
        index = restore_index(rows[0]["index_payload"])
        if (
            index.region_id != region_id
            or index.criterion_id != criterion_id
            or index.run_id != head.run_id
            or index.basis != basis
            or index.measurement_definition != head.measurement_definition
            or index.measurement_definition != basis.required_measurement_definition
        ):
            return None
        return index

    def save(self, summary: IndexSummary) -> None:
        body = f"INSERT INTO {self.summary_table} SETTINGS max_threads=1,max_insert_threads=1 FORMAT JSONEachRow\n"
        record = asdict(summary)
        index = record.pop("index")
        record["index_payload"] = json.dumps(index, allow_nan=False) if index else ""
        request = Request(
            self.reader.url + "/",
            data=body.encode() + json.dumps(record, allow_nan=False).encode(),
            headers={k: v for k, v in self.reader.headers.items() if k != "Accept-Encoding"},
        )
        try:
            with urlopen(request, timeout=60) as response:
                response.read()
        except OSError as error:
            raise DataUnavailable("Index summary storage is unavailable") from error


def restore_index(payload: str) -> RegionalIndex:
    record = json.loads(payload)
    record["measurement_definition"] = MeasurementDefinition(
        record.get("measurement_definition", MeasurementDefinition.SINGLE_REFERENCE_POINT)
    )
    basis = record["basis"]
    record["basis"] = basis_from_record(basis)
    for stage in ("baseline", "scenario"):
        record[stage] = [IndexValue(**row) for row in record[stage]]
    return RegionalIndex(**record)


def restore_summary(row: dict[str, Any]) -> IndexSummary:
    record = dict(row)
    payload = record.pop("index_payload")
    record["index"] = restore_index(str(payload)) if payload else None
    return IndexSummary(**record)
