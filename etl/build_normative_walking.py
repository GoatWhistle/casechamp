import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import osmium

from analytics.client import ClickHouse
from normative_walking.extract import Extractor

ROOT = Path(__file__).resolve().parent.parent
RULES = "pedestrian-v2"
SOURCE = "https://download.openstreetmap.fr/extracts/russia/ural_federal_district/kurgan_oblast-latest.osm.pbf"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/normative-walking")
    parser.add_argument("--import-storage", action="store_true")
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    digest = hashlib.sha256(args.pbf.read_bytes()).hexdigest()
    revision = hashlib.sha256((digest + RULES).encode()).hexdigest()[:24]
    folder = args.output / revision
    folder.mkdir(parents=True, exist_ok=True)
    if args.reuse:
        previous = json.loads((folder / "manifest.json").read_text())
        if previous["source_sha256"] != digest or previous["rules_version"] != RULES:
            raise ValueError("Walking cache source or rules mismatch")
        counts = json.loads((folder / "counts.json").read_text())
    else:
        handler = Extractor(folder, revision)
        handler.apply_file(str(args.pbf), locations=True, idx="flex_mem")
        counts = handler.finish(folder)
    timestamp = next(line.split("=", 1)[1].replace("\\:", ":")
                     for line in args.state.read_text().splitlines() if line.startswith("timestamp="))
    with osmium.io.Reader(str(args.pbf)) as source:
        if source.header().get("osmosis_replication_timestamp") != timestamp:
            raise ValueError("PBF header and replication state timestamps do not match")
    metadata = {"revision": revision, "created_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "source_url": SOURCE, "source_sha256": digest, "source_timestamp": timestamp,
                "rules_version": RULES, "node_count": counts["nodes"],
                "edge_count": counts["edges"], "origin_count": counts["residential_buildings"],
                "excluded_counts": {key: value for key, value in counts.items()
                                    if key not in ("nodes", "edges", "residential_buildings")}}
    (folder / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata), flush=True)
    if not args.import_storage:
        return
    client = ClickHouse()
    for statement in ((ROOT / "infra/clickhouse/normative-walking.sql").read_text() + "\n" + (ROOT / "infra/clickhouse/normative-pedestrian-regions.sql").read_text()).split(";"):
        if statement.strip():
            client.request(statement)
    existing = client.rows("SELECT revision FROM plexus_normative.pedestrian_networks "
                           f"WHERE revision='{revision}' LIMIT 1")
    if existing:
        raise ValueError("Walking network revision is already imported")
    for name in ("nodes", "edges", "origins"):
        table = "plexus_normative.pedestrian_" + name
        client.request(f"ALTER TABLE {table} DELETE WHERE revision='{revision}' SETTINGS mutations_sync=1")
        client.parquet(table, folder / f"{name}.parquet")
    client.request("INSERT INTO plexus_normative.pedestrian_networks FORMAT JSONEachRow",
                   json.dumps(metadata).encode())
    binding = {"region_id": "37000000", "region_name": "Курганская область", "purpose": "pilot",
               "revision": revision, "published_at": metadata["created_at"], "boundary_sha256": ""}
    client.request("INSERT INTO plexus_normative.pedestrian_regions FORMAT JSONEachRow", json.dumps(binding, ensure_ascii=False).encode())
    print("Walking network imported", revision)


if __name__ == "__main__":
    main()
