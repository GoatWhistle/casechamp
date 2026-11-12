import json
import os
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from synthetic_traffic.geography_queue_store import connect, exclusive, now
from synthetic_traffic.geography_queue_worker import run_queue
from synthetic_traffic.geography_tile import fetch_tile

ROOT = Path("/Users/andreykuronskin/keys_champ/data/traffic-geography-national")
TOKEN = "stavropol-retry-" + uuid.uuid4().hex
STOP = ROOT / "STOP"
EXPECTED_PID = 85705


def write_state(phase, **details):
    path = Path("/private/tmp/plexus-geography/data/southern-fallback/retry-state.json")
    path.write_text(
        json.dumps(
            {"phase": phase, "pid": os.getpid(), "updated_at": now(), **details},
            indent=2,
        )
    )
    print(phase, details, flush=True)


def main():
    previous = json.loads((ROOT / "worker-process.json").read_text())
    if previous.get("pid") != EXPECTED_PID:
        raise RuntimeError("Queue owner changed; do not pause an unexpected worker")
    if STOP.exists():
        raise RuntimeError("A pre-existing stop request must be preserved")
    with STOP.open("x") as marker:
        marker.write(TOKEN)
    write_state("waiting_for_graceful_stop", old_pid=EXPECTED_PID)
    for _ in range(180):
        if STOP.read_text() != TOKEN:
            raise RuntimeError("Stop request changed; preserve the newer user request")
        try:
            with exclusive(ROOT), connect(ROOT) as db:
                with db:
                    changed = db.execute(
                        "UPDATE tiles SET status='pending',attempts=0,last_error='',updated_at=? WHERE active=1 AND status='failed' AND instr(region_ids,'\"07000000\"')>0",
                        (now(),),
                    ).rowcount
                break
        except RuntimeError:
            time.sleep(1)
    else:
        if STOP.exists() and STOP.read_text() == TOKEN:
            STOP.unlink()
        raise RuntimeError("Queue worker did not stop gracefully within180seconds")
    if STOP.read_text() != TOKEN:
        raise RuntimeError("Do not remove a newer user stop request")
    STOP.unlink()
    metadata = {
        "pid": os.getpid(),
        "command": [sys.executable, *sys.argv],
        "operation": "geography_queue run",
        "output": str(ROOT),
        "vector_cache": str(ROOT / "vector-cache-union.sqlite"),
        "stop_file": str(STOP),
        "replaces_pid": EXPECTED_PID,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    temporary = ROOT / "worker-process.json.tmp"
    temporary.write_text(json.dumps(metadata, indent=2))
    temporary.replace(ROOT / "worker-process.json")
    write_state(
        "running_with_active_network_execution", reset_stavropol_failures=changed
    )
    run_queue(ROOT, fetch_tile, vector_cache=ROOT / "vector-cache-union.sqlite")


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        write_state("failed", error=f"{type(error).__name__}: {error}")
        raise
