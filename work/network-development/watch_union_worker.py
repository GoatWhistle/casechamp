import json
import os
import signal
import sqlite3
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from shapely.geometry import box, shape
from synthetic_traffic.geography_queue_store import connect, exclusive, now

REPO = Path("/Users/andreykuronskin/keys_champ")
DATA = REPO / "data/traffic-geography-national"
UNION = DATA / "vector-cache-union.sqlite"
OLD_PID = 72716
LOG = Path("/private/tmp/plexus-geography/data/southern-fallback/worker-switch.json")


def record(state, **details):
    payload = {"state": state, "updated_at": datetime.now(UTC).isoformat(), **details}
    LOG.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload), flush=True)


def switch():
    while (
        not UNION.exists() or not (DATA / "vector-cache-union.manifest.json").exists()
    ):
        if (DATA / "STOP").exists():
            record("skipped_stop_requested")
            return
        pipeline_state = LOG.with_name("state.json")
        if (
            pipeline_state.exists()
            and json.loads(pipeline_state.read_text()).get("phase") == "failed"
        ):
            record("skipped_pipeline_failed")
            return
        time.sleep(5)
    with sqlite3.connect(UNION.resolve().as_uri() + "?mode=ro", uri=True) as db:
        manifest = json.loads(
            db.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0]
        )
        if (
            manifest.get("status") != "complete"
            or db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
        ):
            raise ValueError("Union cache has not passed integrity validation")
    coverage = shape(manifest["coverage_geometry"])
    with sqlite3.connect(
        (DATA / "queue.sqlite3").resolve().as_uri() + "?mode=ro", uri=True
    ) as db:
        tiles = [
            (identifier, json.loads(bounds))
            for identifier, bounds, regions in db.execute(
                "SELECT id,bbox,region_ids FROM tiles WHERE active=1"
            )
            if "07000000" in json.loads(regions)
        ]
    if len(tiles) != 50 or not all(
        coverage.covers(box(*bounds)) for _, bounds in tiles
    ):
        raise ValueError("Union does not cover all50Stavropoltiles")
    process = json.loads((DATA / "worker-process.json").read_text())
    if process.get("pid") != OLD_PID:
        record(
            "ready_no_switch_worker_changed",
            expected_pid=OLD_PID,
            actual_pid=process.get("pid"),
        )
        return
    command = subprocess.run(
        ["ps", "-p", str(OLD_PID), "-o", "command="],
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    if "synthetic_traffic.geography_queue" not in command or str(DATA) not in command:
        record("ready_no_switch_old_pid_identity_unverified", old_pid=OLD_PID)
        return
    if (DATA / "STOP").exists():
        record("skipped_stop_requested")
        return
    record("stopping_verified_worker", old_pid=OLD_PID, command=command.strip())
    os.kill(OLD_PID, signal.SIGINT)
    for _ in range(60):
        try:
            with exclusive(DATA), connect(DATA) as db:
                with db:
                    changed = db.execute(
                        "UPDATE tiles SET status='pending',attempts=0,last_error='',updated_at=? WHERE active=1 AND status='failed' AND instr(region_ids,'\"07000000\"')>0",
                        (now(),),
                    ).rowcount
                break
        except RuntimeError:
            time.sleep(1)
    else:
        raise RuntimeError("Original worker did not release the queue lock")
    if (DATA / "STOP").exists():
        record("skipped_stop_requested_after_shutdown")
        return
    args = [
        str(REPO / "backend/.venv/bin/python"),
        "-u",
        "-m",
        "synthetic_traffic.geography_queue",
        "run",
        "--output",
        str(DATA),
        "--vector-cache",
        str(UNION),
    ]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    with (DATA / "worker.log").open("ab") as output:
        worker = subprocess.Popen(
            args,
            cwd=REPO,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    payload = {
        "pid": worker.pid,
        "command": args,
        "output": str(DATA),
        "vector_cache": str(UNION),
        "stop_file": str(DATA / "STOP"),
        "replaces_pid": OLD_PID,
        "updated_at": now(),
    }
    temporary = DATA / "worker-process.json.tmp"
    temporary.write_text(json.dumps(payload, indent=2))
    temporary.replace(DATA / "worker-process.json")
    record(
        "switched",
        old_pid=OLD_PID,
        new_pid=worker.pid,
        reset_failed_stavropol_tiles=changed,
        vector_cache=str(UNION),
    )


if __name__ == "__main__":
    try:
        switch()
    except BaseException as error:
        record("failed", error=f"{type(error).__name__}: {error}")
        raise
