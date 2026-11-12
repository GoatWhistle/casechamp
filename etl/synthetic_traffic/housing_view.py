import re

from analytics.client import ClickHouse


def activate_collection(client: ClickHouse, database: str, collection: dict) -> None:
    ids = [record["parquet_sha256"] for record in collection["sources"].values()]
    if not ids or any(not re.fullmatch(r"[a-f0-9]{64}", value) for value in ids):
        raise ValueError("Collection source identifiers must be SHA-256 hashes")
    selected = ",".join("'" + value + "'" for value in ids)
    client.request(f"""CREATE OR REPLACE VIEW {database}.housing_current AS
        SELECT id,argMax(lat,source_id) AS lat,argMax(lon,source_id) AS lon,
        argMax(residential_m2_proxy,source_id) AS residential_m2_proxy,
        argMax(floors_assumed,source_id) AS floors_assumed
        FROM {database}.housing WHERE source_id IN ({selected}) GROUP BY id""")
