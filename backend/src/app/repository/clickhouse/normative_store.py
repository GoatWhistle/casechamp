from dataclasses import asdict
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from uuid import uuid4

import pyarrow as pa
from pyarrow import ipc

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative_schema import SCHEMAS
from app.usecase.normative.dto import Assessment, AssessmentReceipt


class NormativeStore:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def insert(self, table: str, rows: list[dict[str, object]]) -> None:
        schema = SCHEMAS[table]
        data = pa.Table.from_pylist(rows, schema=schema)
        sink = pa.BufferOutputStream()
        with ipc.new_stream(sink, schema) as writer:
            writer.write_table(data)
        columns = ",".join(schema.names)
        body = f"INSERT INTO plexus_normative.{table} ({columns}) FORMAT ArrowStream\n".encode()
        body += sink.getvalue().to_pybytes()
        request = Request(
            self.reader.url + "/",
            data=body,
            headers={k: v for k, v in self.reader.headers.items() if k != "Accept-Encoding"},
        )
        try:
            with urlopen(request, timeout=60) as response:
                response.read()
        except OSError as error:
            raise DataUnavailable("Normative assessment storage is unavailable") from error

    def save(self, assessment: Assessment) -> AssessmentReceipt:
        key = uuid4().hex
        rows = [
            {"run_id": key, "stage": stage, **asdict(row)}
            for stage, records in [
                ("baseline", assessment.baseline_rows),
                ("scenario", assessment.rows),
            ]
            for row in records
        ]
        self.insert("run_rows", rows)
        self.insert("run_facilities", [{"run_id": key, **asdict(f)} for f in assessment.facilities])
        if assessment.walking_facts:
            self.insert(
                "run_walking_facts",
                [{"run_id": key, **asdict(fact)} for fact in assessment.walking_facts],
            )
        if assessment.library_facts:
            self.insert(
                "run_library_facts",
                [{"run_id": key, **asdict(fact)} for fact in assessment.library_facts],
            )
        if assessment.medical_facts:
            self.insert(
                "run_medical_facts",
                [{"run_id": key, **asdict(fact)} for fact in assessment.medical_facts],
            )
        if assessment.fire_facts:
            self.insert(
                "run_fire_facts",
                [{"run_id": key, **asdict(fact)} for fact in assessment.fire_facts],
            )
        if assessment.fire_destinations:
            self.insert(
                "run_fire_destinations",
                [{"run_id": key, **asdict(d)} for d in assessment.fire_destinations],
            )
        if assessment.rule_sets:
            self.insert(
                "run_rule_sets",
                [{"run_id": key, **asdict(group)} for group in assessment.rule_sets],
            )
        c = assessment.criterion
        self.insert("run_criteria", [{"run_id": key, **asdict(c)}])
        created = datetime.now(UTC)
        created = created.replace(microsecond=created.microsecond // 1000 * 1000)
        self.insert(
            "runs",
            [
                {
                    "id": key,
                    "created_at": created,
                    "qualification_as_of": assessment.qualification_as_of,
                    "origin_basis": assessment.origin_basis,
                    "criterion_id": c.id,
                    "act": c.act,
                    "clause": c.clause,
                    "edition_date": c.edition_date,
                    "threshold": c.threshold,
                    "source_url": c.source_url,
                    "graph_revision": assessment.graph_revision,
                    "region": assessment.region,
                    "closed_way_ids": assessment.closed_way_ids,
                    "model_revision": assessment.model_revision,
                    "ignored_way_ids": assessment.ignored_way_ids,
                    "fire_speed_kmh": assessment.fire_profile.speed_kmh
                    if assessment.fire_profile
                    else None,
                    "fire_assumption": assessment.fire_profile.assumption
                    if assessment.fire_profile
                    else None,
                }
            ],
        )
        return AssessmentReceipt(key, created)
