import json
from datetime import UTC, datetime


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def checkpoint(store, run_id, state, status="running"):
    store.insert(
        "runs",
        [
            {
                "run_id": run_id,
                "updated": datetime.now(UTC).replace(tzinfo=None),
                "status": status,
                "record": json_text(state),
            }
        ],
    )


def snapshot(store, run_id):
    name = "plexus_traffic_snapshot_" + run_id
    store.execute(f"CREATE DATABASE IF NOT EXISTS {name}")
    for table, source in [
        ("ways", "plexus_refresh_graph.ways"),
        ("road_lines", "plexus_refresh_graph.road_lines"),
        ("regions", "plexus_atlas.atlas_regions"),
        ("boundaries", "plexus_atlas.atlas_boundaries"),
    ]:
        exists = store.rows(f"EXISTS TABLE {name}.{table}")[0]["result"]
        if exists and int(store.rows(f"SELECT count() n FROM {name}.{table}")[0]["n"]):
            continue
        if exists:
            store.execute(f"DROP TABLE {name}.{table}")
        loading = name + "." + table + "__loading"
        store.execute(f"DROP TABLE IF EXISTS {loading}")
        store.execute(f"CREATE TABLE {loading} AS {source}")
        expected = int(store.rows(f"SELECT count() n FROM {source}")[0]["n"])
        store.execute(f"ALTER TABLE {loading} ATTACH PARTITION ALL FROM {source}")
        actual = int(store.rows(f"SELECT count() n FROM {loading}")[0]["n"])
        if not expected or actual != expected:
            raise ValueError(
                f"Snapshot count mismatch: {table}: {actual} != {expected}"
            )
        store.execute(f"RENAME TABLE {loading} TO {name}.{table}")
    return name


def validate_snapshot(store, name, state):
    for table in ["ways", "road_lines", "regions", "boundaries"]:
        store.execute(f"SYSTEM STOP MERGES {name}.{table}")
    signature = store.rows(f"""SELECT table,name,rows,hash_of_all_files
        FROM system.parts WHERE active AND database='{name}' ORDER BY table,name""")
    previous = state.get("snapshot_signature")
    if previous and previous != signature:
        raise ValueError(
            "Pinned snapshot parts changed; refuse to reuse completed stages"
        )
    state["snapshot_signature"] = signature
