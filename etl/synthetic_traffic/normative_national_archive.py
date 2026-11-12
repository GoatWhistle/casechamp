import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


def archive_region(repo, region_id):
    root = Path(repo) / ".local/normative-regional-walking/networks" / region_id
    candidates = list(root.glob("*/manifest.json"))
    if not candidates:
        raise ValueError("No completed regional pedestrian snapshot exists")
    manifest = max(candidates, key=lambda path: path.stat().st_mtime_ns)
    evidence = json.loads(manifest.read_text())
    files = {}
    for name, field in [
        ("nodes", "node_count"),
        ("edges", "edge_count"),
        ("origins", "origin_count"),
    ]:
        path = manifest.parent / (name + ".parquet")
        rows = pq.ParquetFile(path).metadata.num_rows
        if rows != evidence["metadata"][field]:
            raise ValueError(
                "Durable pedestrian artifact differs from its published count"
            )
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        files[name] = {
            "path": str(path.relative_to(Path(repo))),
            "bytes": path.stat().st_size,
            "rows": rows,
            "sha256": digest.hexdigest(),
        }
    result = {
        "status": "complete",
        "region_id": region_id,
        "revision": evidence["metadata"]["revision"],
        "files": files,
        "source_manifest": str(manifest.relative_to(Path(repo))),
    }
    temporary = manifest.parent / "artifacts.json.part"
    temporary.write_text(json.dumps(result, indent=2))
    temporary.replace(manifest.parent / "artifacts.json")
    return result
