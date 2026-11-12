import json
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path

from app.usecase.municipal_dataset import MunicipalSnapshotSource


def publish_municipal_source(
    directory: Path,
    source: MunicipalSnapshotSource,
    digest: str,
    write: Callable[[Path, bytes], None],
) -> None:
    key = sha256(
        json.dumps((source.region_id, source.criterion_id, source.stage)).encode()
    ).hexdigest()
    record = {
        "region_id": source.region_id,
        "criterion_id": source.criterion_id,
        "stage": source.stage,
        "source_sha256": digest,
        "run_id": source.run_id,
    }
    write(directory / "published" / (key + ".json"), json.dumps(record, sort_keys=True).encode())


def active_municipal_sources(directory: Path) -> set[str]:
    return {
        json.loads(path.read_bytes())["source_sha256"]
        for path in (directory / "published").glob("*.json")
    }


def current_boundary_snapshot(directory: Path, region_id: str) -> str | None:
    path = directory / "boundary-regions" / (sha256(region_id.encode()).hexdigest() + ".json")
    return json.loads(path.read_bytes())["boundary_snapshot_sha256"] if path.exists() else None
