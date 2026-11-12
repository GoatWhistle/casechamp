import json
import os
from pathlib import Path
from shutil import disk_usage
from time import sleep

from synthetic_traffic.geography_queue_store import (
    connect,
    exclusive,
    now,
    state,
    status,
)

MIN_FREE = 15 * 1024**3
MAX_DATA = 30 * 1024**3


def data_bytes(root):
    total = 0
    for directory, _, files in os.walk(root, followlinks=False):
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                try:
                    total += path.stat().st_size
                except FileNotFoundError:
                    continue
    return total


def _wait(root, seconds, pause):
    while seconds > 0:
        if (root / "STOP").exists():
            return False
        interval = min(1.0, seconds)
        pause(interval)
        seconds -= interval
    return not (root / "STOP").exists()


def run_queue(
    output,
    fetch,
    vector_cache=None,
    pause=sleep,
    delay=10.0,
    min_free=MIN_FREE,
    max_data=MAX_DATA,
):
    root = Path(output)
    if not (root / "queue.sqlite3").exists():
        raise ValueError("Plan the atlas geography queue before running it")
    with exclusive(root), connect(root) as db:
        with db:
            db.execute(
                "UPDATE tiles SET status='pending',attempts=MAX(0,attempts-1),updated_at=? WHERE status='running'",
                (now(),),
            )
        state(db, "running")
        waiting = 0.0
        while True:
            if not _wait(root, waiting, pause):
                state(db, "stopped", reason="stop_file")
                break
            free, used = disk_usage(root).free, data_bytes(root)
            if free < min_free or used >= max_data:
                state(
                    db,
                    "diskpaused",
                    free_bytes=free,
                    data_bytes=used,
                    min_free_bytes=min_free,
                    max_data_bytes=max_data,
                )
                break
            row = db.execute(
                "SELECT * FROM tiles WHERE active=1 AND status='pending' ORDER BY priority,id LIMIT 1"
            ).fetchone()
            if row is None:
                failures = db.execute(
                    "SELECT COUNT(*) FROM tiles WHERE active=1 AND status='failed'"
                ).fetchone()[0]
                state(db, "completed_with_failures" if failures else "completed")
                break
            attempt = row["attempts"] + 1
            with db:
                db.execute(
                    "UPDATE tiles SET status='running',attempts=?,updated_at=? WHERE id=?",
                    (attempt, now(), row["id"]),
                )
            state(db, "running", current_tile=row["id"], attempt=attempt)
            destination = root / "tiles" / row["id"]
            destination.mkdir(parents=True, exist_ok=True)
            try:
                selected_cache = (
                    vector_cache
                    if vector_cache is not None
                    and Path(vector_cache).is_file()
                    and "07000000" in json.loads(row["region_ids"])
                    else None
                )
                manifest = fetch(
                    json.loads(row["bbox"]),
                    destination,
                    root / "cache",
                    resolution=0.001,
                    vector_cache=selected_cache,
                )
                artifact = destination / "geography.npz"
                if (
                    not isinstance(manifest, dict)
                    or not artifact.is_file()
                    or artifact.stat().st_size == 0
                ):
                    raise ValueError(
                        "Tile fetch did not produce a complete geography artifact and manifest"
                    )
                encoded = json.dumps(manifest, ensure_ascii=False)
                with db:
                    db.execute(
                        "UPDATE tiles SET status='complete',last_error='',bytes=?,manifest=?,updated_at=? WHERE id=?",
                        (data_bytes(destination), encoded, now(), row["id"]),
                    )
                waiting = delay
            except Exception as error:  # noqa: BLE001 - persist provider failures for bounded retries
                failed = attempt >= 3
                with db:
                    db.execute(
                        "UPDATE tiles SET status=?,last_error=?,updated_at=? WHERE id=?",
                        (
                            "failed" if failed else "pending",
                            f"{type(error).__name__}: {error}",
                            now(),
                            row["id"],
                        ),
                    )
                waiting = delay + (0 if failed else 2 ** (attempt - 1))
    return status(root)
