import json
import re

import pyarrow as pa
from pyarrow import ipc
from road_traffic.storage import Storage

DATABASES = {
    "plexus_graph": "plexus_capacity_graph",
    "plexus_casechamp": "plexus_capacity_casechamp",
    "plexus_atlas": "plexus_capacity_atlas",
}


def mapped(sql):
    for source, target in DATABASES.items():
        sql = sql.replace(source + ".", target + ".")
    return sql


class CapacityStore(Storage):
    def __init__(self):
        super().__init__("plexus_capacity_casechamp")

    def insert_arrow(self, table, values):
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_.]*", table):
            raise ValueError("Invalid output table")
        if not len(values):
            return
        buffer = pa.BufferOutputStream()
        with ipc.new_stream(buffer, values.schema) as writer:
            writer.write_table(values)
        names = ",".join("`" + name + "`" for name in values.column_names)
        with self.response(
            f"INSERT INTO {table} ({names}) FORMAT ArrowStream",
            buffer.getvalue().to_pybytes(),
        ) as response:
            response.read()

    def frame(self, query):
        return pa.Table.from_batches(list(self.batches(query))).to_pandas()

    def fresh(self, table, reference=None):
        loading = table + "__loading"
        self.execute(f"DROP TABLE IF EXISTS {loading}")
        self.execute(f"CREATE TABLE {loading} AS {reference or table}")
        return loading

    def replace(self, loading, target):
        self.execute(f"EXCHANGE TABLES {target} AND {loading}")
        self.execute(f"DROP TABLE {loading}")


def freeze(store, output):
    marker = output / "source.json"
    if marker.exists():
        return json.loads(marker.read_text())
    occupied = store.rows(
        "SELECT count() n FROM system.tables WHERE database IN "
        "('plexus_capacity_graph','plexus_capacity_casechamp','plexus_capacity_atlas')"
    )[0]["n"]
    if int(occupied):
        raise ValueError(
            "Capacity staging already exists without this source checkpoint; "
            "inspect the existing output and activation journal before rebuilding"
        )
    metadata = store.rows("SELECT key,value FROM plexus_atlas.atlas_metadata")
    source_revision = {r["key"]: r["value"] for r in metadata}.get("graph_revision")
    if not source_revision:
        raise ValueError("Active graph revision is unavailable")
    for original, destination in DATABASES.items():
        store.execute(f"CREATE DATABASE IF NOT EXISTS {destination}")
        tables = store.rows(
            f"SELECT name FROM system.tables WHERE database='{original}' AND engine LIKE '%MergeTree' ORDER BY name"
        )
        for row in tables:
            name = row["name"]
            if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name):
                raise ValueError("Unexpected source table")
            target, source = f"{destination}.{name}", f"{original}.{name}"
            if not store.rows(f"EXISTS TABLE {target}")[0]["result"]:
                loading = target + "__loading"
                store.execute(f"DROP TABLE IF EXISTS {loading}")
                store.execute(f"CREATE TABLE {loading} AS {source}")
                store.execute(f"SYSTEM STOP MERGES {loading}")
                expected = int(store.rows(f"SELECT count() n FROM {source}")[0]["n"])
                if expected:
                    store.execute(
                        f"ALTER TABLE {loading} ATTACH PARTITION ALL FROM {source}"
                    )
                actual = int(store.rows(f"SELECT count() n FROM {loading}")[0]["n"])
                if actual != expected:
                    raise ValueError(f"Snapshot changed: {source}")
                store.execute(f"RENAME TABLE {loading} TO {target}")
    for table in [
        "idx_np",
        "np_access",
        "idx_region",
        "idx_mo",
        "idx_theil",
        "idx_np_gap",
        "np_city_times",
    ]:
        target = "plexus_capacity_casechamp.reference_" + table
        source = "plexus_capacity_casechamp." + table
        if not store.rows(f"EXISTS TABLE {target}")[0]["result"]:
            loading = target + "__loading"
            store.execute(f"DROP TABLE IF EXISTS {loading}")
            store.execute(f"CREATE TABLE {loading} AS {source}")
            store.execute(f"SYSTEM STOP MERGES {loading}")
            store.execute(f"ALTER TABLE {loading} ATTACH PARTITION ALL FROM {source}")
            store.execute(f"RENAME TABLE {loading} TO {target}")
    current = {
        r["key"]: r["value"]
        for r in store.rows("SELECT key,value FROM plexus_atlas.atlas_metadata")
    }.get("graph_revision")
    if current != source_revision:
        raise ValueError("Active source changed while freezing")
    result = {
        "source_revision": source_revision,
        "routing_policy": "legacy_undirected_72h_trunk_all_scenarios",
        "databases": DATABASES,
    }
    marker.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result
