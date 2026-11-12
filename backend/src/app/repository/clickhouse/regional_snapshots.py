from collections.abc import Sequence
from dataclasses import asdict
from time import sleep
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pyarrow as pa
from pyarrow import ipc

from app.domain.errors import DataUnavailable
from app.domain.normative.model import AccessRow, Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative_schema import SCHEMAS

BATCH_SIZE = 8192


class RegionalSnapshots:
    def __init__(self, reader: ClickHouseReader, prefix: str) -> None:
        self.reader = reader
        self.prefix = prefix

    def save_rows(self, run_id: str, stage: str, rows: Sequence[AccessRow]) -> None:
        schema = SCHEMAS["run_rows"].append(pa.field("position", pa.uint32()))
        for start in range(0, len(rows), BATCH_SIZE):
            self.insert(
                "rows",
                schema,
                [
                    {"run_id": run_id, "stage": stage, "position": start + i, **asdict(row)}
                    for i, row in enumerate(rows[start : start + BATCH_SIZE])
                ],
            )

    def save_facilities(self, run_id: str, facilities: Sequence[Facility]) -> None:
        schema = SCHEMAS["run_facilities"].append(pa.field("position", pa.uint32()))
        for start in range(0, len(facilities), BATCH_SIZE):
            self.insert(
                "facilities",
                schema,
                [
                    {"run_id": run_id, "position": start + i, **asdict(row)}
                    for i, row in enumerate(facilities[start : start + BATCH_SIZE])
                ],
            )

    def insert(self, kind: str, schema: pa.Schema, rows: list[dict[str, object]]) -> None:
        sink = pa.BufferOutputStream()
        with ipc.new_stream(sink, schema) as writer:
            writer.write_table(pa.Table.from_pylist(rows, schema=schema))
        columns = ",".join(schema.names)
        body = f"INSERT INTO {self.prefix}_{kind} ({columns}) SETTINGS max_threads=1,max_insert_threads=1,input_format_parallel_parsing=0 FORMAT ArrowStream\n"
        request = Request(
            self.reader.url + "/",
            data=body.encode() + sink.getvalue().to_pybytes(),
            headers={k: v for k, v in self.reader.headers.items() if k != "Accept-Encoding"},
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=60) as response:
                    response.read()
                return
            except HTTPError as error:
                detail = error.read()
                if b"MEMORY_LIMIT_EXCEEDED" in detail and attempt < 2:
                    sleep(2 * (attempt + 1))
                    continue
                raise DataUnavailable(
                    "Regional measurement snapshot storage is unavailable"
                ) from error
            except OSError as error:
                raise DataUnavailable(
                    "Regional measurement snapshot storage is unavailable"
                ) from error

    def load(self, run_id: str, kind: str, count: int, stage: str = "") -> list[dict[str, Any]]:
        schema = SCHEMAS["run_rows" if kind == "rows" else "run_facilities"]
        columns = ",".join(name for name in schema.names if name not in {"run_id", "stage"})
        clause = " AND stage={stage:String}" if kind == "rows" else ""
        table = self.reader.arrow(
            f"SELECT position,{columns} FROM {self.prefix}_{kind} WHERE run_id={{run:String}}"
            + clause
            + " ORDER BY position",
            {"run": run_id, "stage": stage},
        )
        rows: list[dict[str, Any]] = table.to_pylist()
        if len(rows) != count or any(row.pop("position") != i for i, row in enumerate(rows)):
            raise DataUnavailable("The regional measurement snapshot is incomplete")
        return rows
