import argparse
import json
import os
from pathlib import Path
from time import monotonic, sleep
from urllib.request import Request, urlopen

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_queries import QUERIES
from app.settings import load_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8817")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--parent")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_settings(os.environ)
    reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    rows = reader.rows(QUERIES["references"], {"references": [args.reference]})
    ways = sorted({int(row["way_id"]) for row in rows})
    if not ways:
        raise RuntimeError("Road reference not present in the current snapshot")
    url = args.api.rstrip("/") + "/api/v1/road-stress-tests"
    body = json.dumps({"way_ids": ways, "parent_id": args.parent}).encode()
    started = monotonic()
    with urlopen(Request(url, data=body, headers={"Content-Type": "application/json"}), timeout=180) as response:
        job = json.load(response)
    print(job["id"], flush=True)
    while job["status"] in {"queued", "running"}:
        sleep(2)
        with urlopen(url + "/" + job["id"], timeout=180) as response:
            job = json.load(response)
        print(job["stage"], job["completed"], job["total"], flush=True)
    args.output.write_text(json.dumps({"job": job, "elapsed_seconds": monotonic() - started},
                                     ensure_ascii=False, indent=2) + "\n")
    if job["status"] != "completed":
        raise RuntimeError(job.get("error") or job["status"])


if __name__ == "__main__":
    main()
