import argparse
import gzip
import hashlib
import http.client
import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from client import ClickHouse

DEFAULT_TABLES = [
    f"plexus_graph.{name}"
    for name in ("nodes", "edges", "ways", "locations", "road_costs")
] + ["plexus_atlas.atlas_metadata"]
MIN_FREE_BYTES = 15 * 1024**3
CHUNK_BYTES = 1024**2
TABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*")


def check_space(directory: Path) -> None:
    if shutil.disk_usage(directory).free < MIN_FREE_BYTES:
        raise RuntimeError("Snapshot export requires at least 15 GiB free space")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def table_info(client: ClickHouse, table: str) -> tuple[int, str]:
    if TABLE_NAME.fullmatch(table) is None:
        raise ValueError(f"Invalid table name: {table}")
    rows = int(client.rows(f"SELECT count() AS n FROM {table}")[0]["n"])
    schema = str(client.rows(f"SHOW CREATE TABLE {table}")[0]["statement"])
    database, name = table.split(".")
    for quote in ("`", '"'):
        schema = schema.replace(
            f"{quote}{database}{quote}.{quote}{name}{quote}", table, 1
        )
    if not schema.startswith((f"CREATE TABLE {table}", f"CREATE VIEW {table}")):
        raise RuntimeError(f"Unsupported snapshot schema for {table}")
    return rows, schema


def write_manifest(directory: Path, manifest: dict) -> None:
    temporary = directory / "manifest.json.tmp"
    with temporary.open("w") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(directory / "manifest.json")


def stream_native(client: ClickHouse, table: str, path: Path) -> None:
    connection_type = (
        http.client.HTTPSConnection
        if client.url.scheme == "https"
        else http.client.HTTPConnection
    )
    connection = connection_type(client.url.hostname, client.url.port, timeout=1800)
    query = urlencode(
        {
            "query": f"SELECT * FROM {table} FORMAT Native",
            "readonly": 1,
            "max_threads": 1,
            "buffer_size": CHUNK_BYTES,
            "wait_end_of_query": 0,
            "http_write_exception_in_output_format": 0,
        }
    )
    try:
        connection.request(
            "POST",
            (client.url.path.rstrip("/") or "") + "/?" + query,
            body=b"",
            headers=client.headers,
        )
        response = connection.getresponse()
        if response.status != 200:
            message = response.read(2048).decode(errors="replace")
            raise RuntimeError(
                f"Export failed for {table}: HTTP {response.status}: {message}"
            )
        exception_tag = response.getheader("X-ClickHouse-Exception-Tag")
        marker = (
            b"__exception__\r\n" + exception_tag.encode() if exception_tag else None
        )
        tail = b""
        with path.open("wb") as raw:
            with gzip.GzipFile(
                filename="", mode="wb", compresslevel=3, fileobj=raw, mtime=0
            ) as compressed:
                while chunk := response.read(CHUNK_BYTES):
                    check_space(path.parent)
                    window = tail + chunk
                    tagged = marker is not None and marker in window
                    legacy = re.search(
                        rb"(?:^|\n)Code:\s+\d+\.\s+DB::Exception:", window
                    )
                    if tagged or legacy:
                        raise RuntimeError(
                            f"ClickHouse returned an exception inside the Native stream for {table}"
                        )
                    tail = window[-32768:]
                    compressed.write(chunk)
            raw.flush()
            os.fsync(raw.fileno())
    finally:
        connection.close()


def verify_saved(directory: Path, entry: dict, rows: int, schema: str) -> None:
    asset = entry["asset"]
    if not isinstance(asset, str) or Path(asset).name != asset:
        raise RuntimeError("Invalid snapshot asset path")
    path = directory / asset
    if entry["rows"] != rows or entry["schema"] != schema:
        raise RuntimeError(
            f"Source changed for {entry['table']}; use a new snapshot directory"
        )
    if (
        not path.is_file()
        or path.stat().st_size != entry["bytes"]
        or digest(path) != entry["sha256"]
    ):
        raise RuntimeError(f"Snapshot asset failed integrity verification: {asset}")


def export_snapshot(client: ClickHouse, directory: Path, tables: list[str]) -> dict:
    tables = list(dict.fromkeys(tables))
    if not tables or any(TABLE_NAME.fullmatch(table) is None for table in tables):
        raise ValueError("Specify valid database.table names")
    directory.mkdir(parents=True, exist_ok=True)
    check_space(directory)
    manifest_path = directory / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {
            "format": "clickhouse-native-gzip-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "consistency": "Independent table reads; source row count and DDL checked before and after each export",
            "tables": [],
        }
    )
    entries = {entry["table"]: entry for entry in manifest["tables"]}
    for table in tables:
        check_space(directory)
        rows, schema = table_info(client, table)
        if table in entries:
            verify_saved(directory, entries[table], rows, schema)
            print(f"Verified {table}: {rows} rows", flush=True)
            continue
        asset = table.replace(".", "__") + ".native.gz"
        final = directory / asset
        temporary = directory / (asset + ".part")
        try:
            stream_native(client, table, temporary)
            if table_info(client, table) != (rows, schema):
                raise RuntimeError(f"Source changed while exporting {table}")
            entry = {
                "table": table,
                "asset": asset,
                "bytes": temporary.stat().st_size,
                "sha256": digest(temporary),
                "rows": rows,
                "schema": schema,
                "staging": "__loading" in table or table.endswith("_staging"),
            }
            check_space(directory)
            temporary.replace(final)
            manifest["tables"].append(entry)
            write_manifest(directory, manifest)
            entries[table] = entry
            print(f"Exported {table}: {rows} rows, {entry['bytes']} bytes", flush=True)
        finally:
            temporary.unlink(missing_ok=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--tables", nargs="+", default=DEFAULT_TABLES)
    args = parser.parse_args()
    tables = [table for item in args.tables for table in item.split(",") if table]
    export_snapshot(ClickHouse(), args.directory, tables)


if __name__ == "__main__":
    main()
