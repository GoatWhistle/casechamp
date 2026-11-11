import argparse
import copy
import json
import re
import shlex
from pathlib import Path
from urllib.parse import urlsplit

import pyarrow as pa
from pyarrow import ipc
from road_traffic.snapshot import checkpoint, json_text, snapshot, validate_snapshot
from road_traffic.storage import TABLES, Storage

SOURCE_TABLES = {
    "ways": ("plexus_refresh_graph.ways", ["way_id", "way_idx", "source_tags"]),
    "road_lines": ("plexus_refresh_graph.road_lines", ["way_id", "coordinates"]),
    "regions": (
        "plexus_atlas.atlas_regions",
        ["id", "name", "settlements", "population", "ordinal"],
    ),
    "boundaries": (
        "plexus_atlas.atlas_boundaries",
        ["id", "name", "bounds", "polygons", "ordinal"],
    ),
}
QUERY_LIMITS = " SETTINGS max_threads=1,max_memory_usage=600000000"


class PublicationStorage(Storage):
    def __init__(self, path: Path, port: int):
        values = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            words = shlex.split(line.removeprefix("export "), comments=False)
            if not words:
                continue
            if (len(words) > 1 and not words[1].startswith("#")) or "=" not in words[0]:
                raise ValueError("Expected literal KEY=value environment entries")
            key, value = words[0].split("=", 1)
            values[key] = value
        url = values.get("CLICKHOUSE_URL", f"http://127.0.0.1:{port}")
        parsed = urlsplit(url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.port != port
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                f"Expected only the local ClickHouse endpoint on port {port}"
            )
        self.database = "plexus_traffic"
        self.url = url.rstrip("/")
        self.headers = {
            "X-ClickHouse-User": values.get("CLICKHOUSE_USER", "plexus"),
            "X-ClickHouse-Key": values["CLICKHOUSE_PASSWORD"],
        }


def signature(store, table, columns, predicate="1"):
    fields = ",".join(columns)
    row = store.rows(
        f"SELECT count() AS rows,sum(cityHash64(tuple({fields}))) AS city_sum,"
        f"groupBitXor(sipHash64(tuple({fields}))) AS sip_xor FROM {table} "
        f"WHERE {predicate}" + QUERY_LIMITS
    )[0]
    return {key: str(value) for key, value in row.items()}


def source_state(store, run_id):
    rows = store.rows(
        f"SELECT status,record FROM {store.database}.runs FINAL "
        f"WHERE run_id='{run_id}'" + QUERY_LIMITS
    )
    if len(rows) != 1 or rows[0]["status"] != "completed":
        raise ValueError("Source run must be completed before publication")
    state = json.loads(rows[0]["record"])
    if not state.get("graph_revision") or not state.get("report"):
        raise ValueError("Source run lacks a validated report or graph revision")
    if any(
        stage not in state.get("stages", {})
        for stage in ["attributes", "coverage", "observations"]
    ):
        raise ValueError("Source run has incomplete stages")
    if state.get("snapshot") != "plexus_traffic_snapshot_" + run_id:
        raise ValueError("Source run snapshot identity differs")
    return state


def validate_source_parts(store, state):
    actual = store.rows(
        "SELECT table,name,rows,hash_of_all_files FROM system.parts "
        f"WHERE active AND database='{state['snapshot']}' ORDER BY table,name"
        + QUERY_LIMITS
    )
    if not state.get("snapshot_signature") or actual != state["snapshot_signature"]:
        raise ValueError("Source pinned snapshot physical signature differs")


def columns(store, table):
    return {row["name"]: row["type"] for row in store.rows("DESCRIBE TABLE " + table)}


def copy_table(source, target, name, run_id, fields):
    source_name = source.database + "." + name
    target_name = target.database + "." + name
    predicate = f"run_id='{run_id}'"
    expected = signature(source, source_name, fields, predicate)
    target.clear(name, run_id)
    query = (
        f"SELECT {','.join(fields)} FROM {source_name} WHERE {predicate}"
        + QUERY_LIMITS
        + ",max_block_size=20000"
    )
    for batch in source.batches(query):
        buffer = pa.BufferOutputStream()
        with ipc.new_stream(buffer, batch.schema) as writer:
            writer.write_batch(batch)
        target.execute_insert(name, fields, buffer.getvalue().to_pybytes())
    actual = signature(target, target_name, fields, predicate)
    if actual != expected:
        raise ValueError("Traffic table readback signature mismatch: " + name)
    print(json_text({"table": name, "verified": actual}), flush=True)
    return expected


def publish(run_id, source_env, target_env, output):
    if not re.fullmatch(r"[A-Za-z0-9]{1,40}", run_id):
        raise ValueError("Invalid traffic run identifier")
    source = PublicationStorage(source_env, 18124)
    target = PublicationStorage(target_env, 18123)
    original = source_state(source, run_id)
    validate_source_parts(source, original)
    name = original["snapshot"]
    logical = {}
    for table, (primary, fields) in SOURCE_TABLES.items():
        expected = signature(source, name + "." + table, fields)
        if expected != signature(target, primary, fields):
            raise ValueError("Primary graph lineage differs: " + table)
        logical[table] = expected
    if logical["regions"]["rows"] != "82":
        raise ValueError("Expected exactly 82 source regions")
    target.initialize()
    previous = target.rows(
        f"SELECT record FROM {target.database}.runs FINAL WHERE run_id='{run_id}'"
    )
    if (
        previous
        and json.loads(previous[0]["record"]).get("graph_revision")
        != original["graph_revision"]
    ):
        raise ValueError("Destination run identifier belongs to another graph revision")
    pinned = snapshot(target, run_id)
    for table, (_, fields) in SOURCE_TABLES.items():
        if logical[table] != signature(target, pinned + "." + table, fields):
            raise ValueError("Destination pinned snapshot lineage differs: " + table)
    state = copy.deepcopy(original)
    state.pop("snapshot_signature", None)
    state.pop("error", None)
    state["snapshot"] = pinned
    validate_snapshot(target, pinned, state)
    state["publication"] = {
        "source_url": source.url,
        "destination_url": target.url,
        "source_state": original,
        "source_logical_signatures": logical,
        "signature_method": "row count; unsigned sum of cityHash64(tuple); XOR of sipHash64(tuple)",
        "tables": {},
    }
    checkpoint(target, run_id, state, "running")
    try:
        for table in TABLES:
            if table == "runs":
                continue
            fields = columns(source, source.database + "." + table)
            if fields != columns(target, target.database + "." + table):
                raise ValueError("Traffic table schemas differ: " + table)
            state["publication"]["tables"][table] = copy_table(
                source, target, table, run_id, list(fields)
            )
        results = state["publication"]["tables"]
        if results["road_attributes"]["rows"] != logical["ways"]["rows"]:
            raise ValueError("Road attribute count differs from pinned ways")
        if results["regional_coverage"]["rows"] != "82":
            raise ValueError("Destination regional report does not contain 82 rows")
        if source_state(source, run_id) != original:
            raise ValueError("Source completed state changed during publication")
        validate_source_parts(source, original)
        validate_snapshot(target, pinned, state)
        checkpoint(target, run_id, state, "completed")
        status = target.rows(
            f"SELECT status,record FROM {target.database}.runs FINAL WHERE run_id='{run_id}'"
        )
        if (
            len(status) != 1
            or status[0]["status"] != "completed"
            or json.loads(status[0]["record"]) != state
        ):
            raise ValueError("Destination completed run readback mismatch")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json_text({"run_id": run_id, "status": "completed", **state}) + "\n"
        )
    except Exception as error:
        state["publication"]["error"] = str(error)
        checkpoint(target, run_id, state, "failed")
        raise
    print(
        json_text({"run_id": run_id, "status": "completed", "output": str(output)}),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-env", type=Path, required=True)
    parser.add_argument("--target-env", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    publish(args.run_id, args.source_env, args.target_env, args.output)


if __name__ == "__main__":
    main()
