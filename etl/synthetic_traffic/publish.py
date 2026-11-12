import json
import re
from hashlib import sha256
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from analytics.client import ClickHouse
from pyarrow import ipc
from synthetic_traffic.housing_view import activate_collection
from synthetic_traffic.source import load_network

DATABASE = "plexus_synthetic_traffic"


def insert(client: ClickHouse, table: str, data: pa.Table) -> None:
    sink = pa.BufferOutputStream()
    with ipc.new_stream(sink, data.schema) as stream:
        stream.write_table(data)
    client.request(
        f"INSERT INTO {DATABASE}.{table} FORMAT ArrowStream",
        sink.getvalue().to_pybytes(),
    )


def initialize(client: ClickHouse) -> None:
    client.request(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    tables = {
        "housing_sources": "source_id String, record String",
        "housing_collections": "collection_id String, record String",
        "housing": "source_id String,id String,lat Float64,lon Float64,residential_m2_proxy Float64,floors_assumed Bool",
        "runs": "run_id String,report String",
        "demand": "run_id String,origin_node Int64,destination_node Int64,vehicles_per_hour Float64",
        "flows": "run_id String,variant String,multiplier Float64,way_id Int64,source_node Int64,target_node Int64,flow Float64,hours Float64,demand_capacity_ratio Float64",
    }
    keys = {
        "housing_sources": "source_id",
        "housing_collections": "collection_id",
        "housing": "source_id,id",
        "runs": "run_id",
        "demand": "run_id,origin_node,destination_node",
        "flows": "run_id,variant,multiplier,way_id,source_node,target_node",
    }
    for name, fields in tables.items():
        client.request(
            f"CREATE TABLE IF NOT EXISTS {DATABASE}.{name} ({fields}) ENGINE=MergeTree ORDER BY ({keys[name]})"
        )


def publish_homes(path: Path) -> dict:
    client = ClickHouse()
    initialize(client)
    files = sorted(path.glob("*.parquet")) if path.is_dir() else [path]
    if path.is_dir() and (path / "collection.json").exists():
        collection = json.loads((path / "collection.json").read_text())
        files = [
            path / f"{name}.parquet"
            for name, record in collection["sources"].items()
            if record["status"] == "complete"
        ]
    if not files:
        raise ValueError("No residential Parquet files found")
    report = {}
    for file in files:
        source_id = sha256(file.read_bytes()).hexdigest()
        expected = pq.read_metadata(file).num_rows
        if path.is_dir() and (path / "collection.json").exists():
            source = collection["sources"][file.stem]
            if (
                source["parquet_sha256"] != source_id
                or source["residential_buildings"] != expected
            ):
                raise ValueError("Housing file does not match the verified collection")
        existing = int(
            client.rows(
                f"SELECT count() n FROM {DATABASE}.housing WHERE source_id='{source_id}'"
            )[0]["n"]
        )
        if existing not in {0, expected}:
            raise ValueError(f"Incomplete housing import needs inspection: {source_id}")
        if existing == 0:
            print(f"Publishing {file.name}: {expected} buildings", flush=True)
            for batch in pq.ParquetFile(file).iter_batches(batch_size=50000):
                data = pa.Table.from_batches([batch])
                data = data.append_column(
                    "source_id", pa.array([source_id] * len(data))
                )
                insert(
                    client,
                    "housing",
                    data.select(
                        [
                            "source_id",
                            "id",
                            "lat",
                            "lon",
                            "residential_m2_proxy",
                            "floors_assumed",
                        ]
                    ),
                )
            actual = int(
                client.rows(
                    f"SELECT count() n FROM {DATABASE}.housing WHERE source_id='{source_id}'"
                )[0]["n"]
            )
            if actual != expected:
                raise ValueError("Published housing count does not match source")
            insert(
                client,
                "housing_sources",
                pa.table(
                    {
                        "source_id": [source_id],
                        "record": [
                            json.dumps(
                                {
                                    "file": file.name,
                                    "rows": expected,
                                    "parquet_sha256": source_id,
                                    "extraction": json.loads(
                                        file.with_suffix(".json").read_text()
                                    )
                                    if file.with_suffix(".json").exists()
                                    else {},
                                    "collection": json.loads(
                                        (file.parent / "collection.json").read_text()
                                    )
                                    .get("sources", {})
                                    .get(file.stem, {})
                                    if (file.parent / "collection.json").exists()
                                    else {},
                                }
                            )
                        ],
                    }
                ),
            )
        report[file.name] = {"source_id": source_id, "rows": expected}
    if path.is_dir() and (path / "collection.json").exists():
        record = (path / "collection.json").read_text()
        if json.loads(record)["status"] == "complete":
            activate_collection(client, DATABASE, json.loads(record))
            collection_id = sha256(record.encode()).hexdigest()
            exists = int(
                client.rows(
                    f"SELECT count() n FROM {DATABASE}.housing_collections WHERE collection_id='{collection_id}'"
                )[0]["n"]
            )
            if not exists:
                insert(
                    client,
                    "housing_collections",
                    pa.table({"collection_id": [collection_id], "record": [record]}),
                )
    return report


def publish_run(path: Path, snapshot: Path, run_id: str) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", run_id):
        raise ValueError(
            "Use a run ID of 1-100 letters, digits, hyphens or underscores"
        )
    report = json.loads((path / "report.json").read_text())
    if report.get("status") != "complete":
        raise ValueError("Only completed results can be published")
    demand_text = (path / "demand.json").read_text()
    if sha256(demand_text.encode()).hexdigest() != report["demand_sha256"]:
        raise ValueError("Demand matrix checksum does not match the report")
    demand = json.loads(demand_text)
    network = load_network(snapshot)
    client = ClickHouse()
    initialize(client)
    for name in ["runs", "demand", "flows"]:
        if int(
            client.rows(
                f"SELECT count() n FROM {DATABASE}.{name} WHERE run_id='{run_id}'"
            )[0]["n"]
        ):
            raise ValueError("Run ID already exists; choose a new immutable run ID")
    matrix = pa.table(
        {
            "run_id": [run_id] * len(demand),
            "origin_node": [int(network.raw_nodes[t["origin"]]) for t in demand],
            "destination_node": [
                int(network.raw_nodes[t["destination"]]) for t in demand
            ],
            "vehicles_per_hour": [t["vehicles_per_hour"] for t in demand],
        }
    )
    insert(client, "demand", matrix)
    flow_rows = 0
    for case in report["cases"]:
        entries = [("baseline", case["baseline"])] + [
            (str(i), p) for i, p in enumerate(case["projects"])
        ]
        for variant, result in entries:
            data = pq.read_table(path / result["edge_flows"])
            if variant != "baseline":
                data = data.rename_columns(
                    [
                        "flow"
                        if c == "flow_after"
                        else "hours"
                        if c == "hours_after"
                        else c
                        for c in data.column_names
                    ]
                )
            columns = [
                "way_id",
                "source_node",
                "target_node",
                "flow",
                "hours",
                "demand_capacity_ratio",
            ]
            data = data.select(columns)
            for key, value in [
                ("run_id", run_id),
                ("variant", variant),
                ("multiplier", float(case["multiplier"])),
            ]:
                data = data.append_column(key, pa.array([value] * len(data)))
            insert(
                client,
                "flows",
                data.select(["run_id", "variant", "multiplier", *columns]),
            )
            flow_rows += len(data)
    insert(
        client,
        "runs",
        pa.table(
            {"run_id": [run_id], "report": [json.dumps(report, ensure_ascii=False)]}
        ),
    )
    actual = client.rows(
        f"SELECT count() n FROM {DATABASE}.flows WHERE run_id='{run_id}'"
    )[0]["n"]
    if int(actual) != flow_rows:
        raise ValueError("Published flow row count does not match the run")
    return {
        "database": DATABASE,
        "run_id": run_id,
        "demand_pairs": len(demand),
        "flow_rows": flow_rows,
    }
