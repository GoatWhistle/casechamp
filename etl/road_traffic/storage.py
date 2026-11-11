import json
import os
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pyarrow as pa
from pyarrow import ipc
from road_traffic.assumptions import initialize_lane_view

TABLES = {
    "runs": "run_id String, updated DateTime64(3), status String, record String",
    "sources": "run_id String, source_id String, record String",
    "road_attributes": """run_id String, way_id Int64, way_idx Int32, highway String,
        lanes_total Nullable(UInt16), lanes_forward Nullable(UInt16),
        lanes_backward Nullable(UInt16), lanes_both_ways Nullable(UInt16),
        lanes_status LowCardinality(String), oneway LowCardinality(String),
        maxspeed_kmh Nullable(Float64), maxspeed_forward_kmh Nullable(Float64),
        maxspeed_backward_kmh Nullable(Float64), direction_status LowCardinality(String),
        maxspeed_status LowCardinality(String), source_tags String, quality Array(String)""",
    "traffic_observations": """run_id String, observation_id String, source_id String,
        region_id String, value Nullable(Float64), unit String, period String, record String""",
    "graph_matches": "run_id String, observation_id String, status String, record String",
    "coverage_parts": """run_id String, region_id String, way_id Int64, km Float64,
        highway LowCardinality(String), lanes_status LowCardinality(String), has_lanes UInt8""",
    "regional_coverage": "run_id String, region_id String, record String",
}
KEYS = {
    "runs": "run_id",
    "road_attributes": "run_id,way_idx",
    "coverage_parts": "run_id,region_id,way_id",
    "traffic_observations": "run_id,region_id,observation_id",
    "regional_coverage": "run_id,region_id",
    "sources": "run_id,source_id",
    "graph_matches": "run_id,observation_id",
}


class Storage:
    def __init__(self, database="plexus_traffic"):
        if not database.replace("_", "").isalnum() or not database[0].isalpha():
            raise ValueError("Invalid database identifier")
        self.database = database
        self.url = os.environ.get("CLICKHOUSE_URL", "http://127.0.0.1:18123")
        self.headers = {
            "X-ClickHouse-User": os.environ.get("CLICKHOUSE_USER", "plexus"),
            "X-ClickHouse-Key": os.environ["CLICKHOUSE_PASSWORD"],
        }

    @contextmanager
    def response(self, sql, body=None):
        query = urlencode({"query": sql}) if body is not None else ""
        request = Request(
            self.url + "/?" + query,
            data=body if body is not None else sql.encode(),
            headers=self.headers,
        )
        try:
            with urlopen(request, timeout=600) as response:
                yield response
        except HTTPError as error:
            raise RuntimeError(error.read().decode()[:2000]) from error

    def execute(self, sql):
        with self.response(sql) as response:
            return response.read()

    def rows(self, sql):
        return [
            json.loads(row)
            for row in self.execute(sql + " FORMAT JSONEachRow").splitlines()
        ]

    def batches(self, sql):
        with self.response(sql + " FORMAT ArrowStream") as response:
            yield from ipc.open_stream(response)

    def initialize(self):
        self.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        for name, fields in TABLES.items():
            engine = "ReplacingMergeTree(updated)" if name == "runs" else "MergeTree"
            self.execute(
                f"CREATE TABLE IF NOT EXISTS {self.database}.{name} ({fields}) "
                f"ENGINE={engine} ORDER BY ({KEYS[name]})"
            )

        for field, kind in {
            "maxspeed_forward_kmh": "Nullable(Float64)",
            "maxspeed_backward_kmh": "Nullable(Float64)",
            "direction_status": "LowCardinality(String)",
            "maxspeed_status": "LowCardinality(String)",
        }.items():
            self.execute(
                f"ALTER TABLE {self.database}.road_attributes ADD COLUMN IF NOT EXISTS {field} {kind}"
            )

        existing = {
            r["name"]: r["type"]
            for r in self.rows(f"DESCRIBE TABLE {self.database}.road_attributes")
        }
        for field in [
            "lanes_total",
            "lanes_forward",
            "lanes_backward",
            "lanes_both_ways",
        ]:
            if existing[field] == "Nullable(Int16)":
                negative = self.rows(
                    f"SELECT countIf({field}<0) n FROM {self.database}.road_attributes"
                )[0]["n"]
                if int(negative):
                    raise ValueError("Negative lane count prevents unsigned migration")
                self.execute(
                    f"ALTER TABLE {self.database}.road_attributes MODIFY COLUMN {field} Nullable(UInt16)"
                )

        initialize_lane_view(self)

    def insert(self, name, rows):
        if not rows:
            return
        schema = self.rows(f"DESCRIBE TABLE {self.database}.{name}")
        fields = {row["name"]: row["type"] for row in schema}
        types = {
            "String": pa.string(),
            "Int64": pa.int64(),
            "Int32": pa.int32(),
            "Int16": pa.int16(),
            "UInt16": pa.uint16(),
            "UInt8": pa.uint8(),
            "Float64": pa.float64(),
            "DateTime64(3)": pa.timestamp("ms"),
            "Array(String)": pa.list_(pa.string()),
        }
        arrow_fields = []
        for key in rows[0]:
            kind = (
                fields[key]
                .replace("Nullable(", "")
                .replace("LowCardinality(", "")
                .rstrip(")")
            )
            if fields[key] == "Array(String)":
                kind = "Array(String)"
            if fields[key] == "DateTime64(3)":
                kind = "DateTime64(3)"
            arrow_fields.append((key, types[kind]))
        table = pa.Table.from_pylist(rows, schema=pa.schema(arrow_fields))
        buffer = pa.BufferOutputStream()
        with ipc.new_stream(buffer, table.schema) as writer:
            writer.write_table(table)
        self.execute_insert(name, list(rows[0]), buffer.getvalue().to_pybytes())

    def execute_insert(self, name, columns, data):
        with self.response(
            f"INSERT INTO {self.database}.{name} ({','.join(columns)}) FORMAT ArrowStream",
            data,
        ) as response:
            response.read()

    def clear(self, name, run_id):
        self.execute(
            f"ALTER TABLE {self.database}.{name} DELETE WHERE run_id='{run_id}' SETTINGS mutations_sync=1"
        )
