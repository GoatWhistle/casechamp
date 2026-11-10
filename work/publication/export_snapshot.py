import gzip
import hashlib
import http.client
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "etl/analytics"))
from client import ClickHouse


def github(arguments):
    for attempt in range(6):
        try:
            return subprocess.check_output(["gh", *arguments])
        except subprocess.CalledProcessError:
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))


TAG = "data-clickhouse-20261110"
REPO = "GoatWhistle/casechamp"
DEST = ROOT / "data/releases" / TAG
DATABASES = (
    "plexus_additional",
    "plexus_atlas",
    "plexus_casechamp",
    "plexus_graph",
    "plexus_refresh_graph",
    "plexus_scenario",
)
DEST.mkdir(parents=True, exist_ok=True)
c = ClickHouse()
manifest_path = DEST / "manifest.json"
manifest = (
    json.loads(manifest_path.read_text())
    if manifest_path.exists()
    else {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "format": "ClickHouse Native, gzip",
        "server_version": c.rows("SELECT version() AS version")[0]["version"],
        "release": TAG,
        "scope": "Dataset databases only. User calculation history and system databases excluded. plexus_refresh_graph is unfinished staging, not the active model.",
        "tables": [],
    }
)
tables = c.rows(
    "SELECT database,name,create_table_query FROM system.tables WHERE database IN "
    + str(DATABASES)
    + " ORDER BY database,name"
)
lock = Lock()
completed_tables = {table["table"] for table in manifest["tables"]}


def export_table(table):
    database, name = table["database"], table["name"]
    assert re.fullmatch(r"[a-zA-Z0-9_]+", database + name)
    qualified = database + "." + name
    if qualified in completed_tables:
        return
    rows = int(c.rows(f"SELECT count() AS n FROM {qualified}")[0]["n"])
    path = DEST / (qualified + ".native.gz")
    connection = http.client.HTTPConnection(c.url.hostname, c.url.port, timeout=1800)
    connection.request(
        "POST",
        "/?" + urlencode({"max_threads": 1}),
        body=f"SELECT * FROM {qualified} FORMAT Native".encode(),
        headers=c.headers,
    )
    response = connection.getresponse()
    if response.status != 200:
        raise RuntimeError(response.read().decode()[:1000])
    with gzip.open(path, "wb", compresslevel=6) as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    summary = json.loads(response.getheader("X-ClickHouse-Summary", "{}"))
    connection.close()
    assert int(c.rows(f"SELECT count() AS n FROM {qualified}")[0]["n"]) == rows
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    size = path.stat().st_size
    github(["release", "upload", TAG, str(path), "-R", REPO, "--clobber"])
    release_id = json.loads(
        github(["release", "view", TAG, "-R", REPO, "--json", "databaseId"])
    )["databaseId"]
    assets = json.loads(github(["api", f"repos/{REPO}/releases/{release_id}"]))[
        "assets"
    ]
    asset = next(item for item in assets if item["name"] == path.name)
    assert asset["size"] == size
    assert asset.get("digest") == "sha256:" + digest, asset.get("digest")
    with lock:
        manifest["tables"].append(
            dict(
                table=qualified,
                rows=rows,
                schema=table["create_table_query"],
                asset=path.name,
                bytes=size,
                sha256=digest,
                staging=database.startswith("plexus_refresh_"),
                exported_at=datetime.now(timezone.utc).isoformat(),
                summary=summary,
            )
        )
        temporary = manifest_path.with_suffix(".loading.json")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(manifest_path)
    print(qualified, rows, size, "uploaded and digest verified", flush=True)
    path.unlink()


with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(export_table, tables))

manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
github(["release", "upload", TAG, str(manifest_path), "-R", REPO, "--clobber"])
print(
    "COMPLETE",
    len(manifest["tables"]),
    sum(t["bytes"] for t in manifest["tables"]),
    flush=True,
)
