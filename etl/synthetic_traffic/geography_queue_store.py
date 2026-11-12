import fcntl
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


@contextmanager
def exclusive(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / ".queue.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(
                "Geography queue is already locked by another process"
            ) from error
        try:
            yield output
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def connect(output):
    db = sqlite3.connect(Path(output) / "queue.sqlite3")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS regions(id TEXT PRIMARY KEY, name TEXT NOT NULL, bounds TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tiles(
            id TEXT PRIMARY KEY, bbox TEXT NOT NULL, region_ids TEXT NOT NULL,
            priority INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT NOT NULL DEFAULT '',
            bytes INTEGER NOT NULL DEFAULT 0, manifest TEXT NOT NULL DEFAULT '{}',
            active INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL
        );
    """)
    return db


def now():
    return datetime.now(UTC).isoformat()


def metadata(db, key, value):
    db.execute(
        "INSERT INTO metadata VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value, ensure_ascii=False)),
    )


def state(db, value, **details):
    with db:
        metadata(db, "runtime", {"state": value, "updated_at": now(), **details})


def status(output):
    path = Path(output) / "queue.sqlite3"
    if not path.exists():
        return {"state": "unplanned", "tiles": {}, "regions": 0}
    with sqlite3.connect(path) as db:
        records = {
            key: json.loads(value)
            for key, value in db.execute("SELECT key,value FROM metadata")
        }
        counts = dict(
            db.execute(
                "SELECT status,COUNT(*) FROM tiles WHERE active=1 GROUP BY status"
            )
        )
        regions = db.execute("SELECT COUNT(*) FROM regions").fetchone()[0]
        stored = db.execute(
            "SELECT COALESCE(SUM(bytes),0) FROM tiles WHERE active=1"
        ).fetchone()[0]
    return {
        **records.get("runtime", {"state": "planned"}),
        "coverage": records.get("coverage", {}),
        "tiles": counts,
        "regions": regions,
        "artifact_bytes": stored,
    }
