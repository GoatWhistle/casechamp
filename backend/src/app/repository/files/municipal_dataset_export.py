import gzip
import json
import os
from collections import Counter
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile


def export_municipal_dataset(directory: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    sources: set[str] = set()
    boundaries: set[str] = set()
    with NamedTemporaryFile(dir=output.parent, delete=False) as temporary:
        temporary_name = temporary.name
        try:
            with gzip.GzipFile(filename="", fileobj=temporary, mode="wb", mtime=0) as compressed:
                for path in sorted((directory / "aggregates").glob("*.json")):
                    record = json.loads(path.read_bytes())
                    if record.get("aggregation_method") != "municipal-aggregate-v3":
                        continue
                    compressed.write(
                        json.dumps(
                            record, sort_keys=True, ensure_ascii=False, allow_nan=False
                        ).encode()
                        + b"\n"
                    )
                    counts[record["value"]["status"]] += 1
                    sources.add(record["source_sha256"])
                    if record.get("boundary_snapshot_sha256"):
                        boundaries.add(record["boundary_snapshot_sha256"])
            temporary.flush()
            os.fsync(temporary.fileno())
            os.replace(temporary_name, output)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
    digest = sha256()
    with output.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    manifest: dict[str, object] = {
        "schema_version": "municipal-dataset-v1",
        "aggregates": sum(counts.values()),
        "statuses": dict(counts),
        "source_snapshots": sorted(sources),
        "boundary_snapshots": sorted(boundaries),
        "boundary_files": [
            "boundaries/" + digest + "/boundaries.json.gz" for digest in sorted(boundaries)
        ],
        "export_sha256": digest.hexdigest(),
        "export_file": output.name,
        "qualification": "per_record_source_qualification_no_regional_proxy",
    }
    target = output.with_suffix(output.suffix + ".manifest.json")
    target.write_text(json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    return manifest
