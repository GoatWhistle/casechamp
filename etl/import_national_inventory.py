import argparse
import gzip
import json
import time
from pathlib import Path

from analytics.client import ClickHouse


def insert_batch(client: ClickHouse, table: str, rows: list[str]) -> None:
    sql = f"INSERT INTO {table} SETTINGS max_threads=1,max_insert_threads=1,input_format_parallel_parsing=0 FORMAT JSONEachRow"
    payload = "\n".join(rows).encode()
    for attempt in range(6):
        try:
            client.request(sql, payload)
            return
        except RuntimeError as error:
            if "MEMORY_LIMIT_EXCEEDED" not in str(error) or attempt == 5:
                raise
            print("retrying memory-limited insert", table, attempt + 1, flush=True)
            time.sleep(min(30, 2 ** (attempt + 1)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", required=True)
    parser.add_argument("--root", type=Path, default=Path(".local/normative-national-inputs"))
    args = parser.parse_args()
    client = ClickHouse()
    for statement in Path("infra/clickhouse/normative-national.sql").read_text().split(";"):
        if statement.strip():
            client.request(statement)
    regions = json.loads((args.root / "regions.json").read_text())["regions"]
    insert_batch(client, "plexus_normative.inventory_regions", [json.dumps({"id": r["id"], "name": r["name"]}, ensure_ascii=False) for r in regions])
    directory = args.root / "derived"
    if not directory.exists():
        directory = args.root / "objects"
    path = directory / (args.district + ".pois.jsonl.gz")
    batch = []
    count = 0
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["region_assignment"] != "spatial_match":
                continue
            tags = row["tags"]
            address = ", ".join(tags[key] for key in ("addr:city", "addr:street", "addr:housenumber") if tags.get(key))
            record = {key: row[key] for key in ("id", "region_id", "region_name", "categories", "latitude", "longitude", "source_url", "snapshot_url", "source_sha256", "observed_at", "geometry_method")}
            record.update(name=row["name"] or "", address=address, version=row["osm_version"], district=args.district)
            batch.append(json.dumps(record, ensure_ascii=False))
            if len(batch) >= 1000:
                insert_batch(client, "plexus_normative.national_inventory", batch)
                count += len(batch)
                batch = []
        if batch:
            insert_batch(client, "plexus_normative.national_inventory", batch)
            count += len(batch)
    print("imported", args.district, count)


if __name__ == "__main__":
    main()
