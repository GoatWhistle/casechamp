import argparse
import hashlib
import json
import socket
from pathlib import Path
from urllib.parse import urlsplit

from .activation_state import position, rollback, save, uuid, verify_plan
from .storage import DATABASES, CapacityStore
from .validate import TABLES, validate


def assert_api_stopped(api_url):
    parsed = urlsplit(api_url)
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            "Activation API URL must reference loopback localhost or 127.0.0.1"
        )
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        connection = socket.create_connection((parsed.hostname, port), timeout=2)
    except ConnectionRefusedError:
        return
    except OSError as error:
        raise ValueError("Cannot establish that the API port is closed") from error
    connection.close()
    raise ValueError("Stop the local API before switching its graph tables")


def make_plan(store, artifact):
    plan = []
    suffix = hashlib.sha256(artifact.encode()).hexdigest()[:16]
    for database, tables in TABLES.items():
        for name in tables:
            active, candidate = f"{database}.{name}", f"{DATABASES[database]}.{name}"
            item = {
                "active": active,
                "candidate": candidate,
                "active_uuid": uuid(store, active),
                "candidate_uuid": uuid(store, candidate),
            }
            if not item["candidate_uuid"]:
                raise ValueError(f"Candidate table is missing: {candidate}")
            if item["active_uuid"] is None:
                item["empty"] = candidate + "__activation_empty_" + suffix
                store.execute(
                    f"CREATE TABLE IF NOT EXISTS {item['empty']} AS {candidate}"
                )
                if int(store.rows(f"SELECT count() n FROM {item['empty']}")[0]["n"]):
                    raise ValueError("Activation placeholder must be empty")
                item["empty_uuid"] = uuid(store, item["empty"])
            plan.append(item)
    return plan


def completed(store, record):
    for item in record["plan"]:
        if position(store, item) != "swapped":
            raise ValueError(
                "Completed activation UUIDs no longer match the live tables"
            )
    rows = store.rows(
        "SELECT value FROM plexus_atlas.atlas_metadata WHERE key='artifact_version'"
    )
    if len(rows) != 1 or rows[0]["value"] != record["artifact_version"]:
        raise ValueError("Completed activation artifact is no longer active")
    return record


def rollback_activation(store, root, api_url):
    assert_api_stopped(api_url)
    path = root / "data/road-capacity/activation.json"
    if not path.exists():
        raise ValueError("No activation journal is available")
    record = json.loads(path.read_text())
    verify_plan(record, TABLES, DATABASES)
    return rollback(store, path, record)


def activate(store, root, api_url):
    path = root / "data/road-capacity/activation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        previous = json.loads(path.read_text())
        verify_plan(previous, TABLES, DATABASES)
        if previous["status"] == "completed":
            return completed(store, previous)
        assert_api_stopped(api_url)
        if previous["status"] != "rolled_back":
            rollback(store, path, previous)
    assert_api_stopped(api_url)
    validation = validate(store, root)
    busy = store.rows(
        "SELECT count() n FROM plexus_state.road_jobs FINAL WHERE status IN ('queued','running')"
    )[0]["n"]
    if int(busy):
        raise ValueError("Persisted calculation queue must be idle before activation")
    record = {
        "status": "prepared",
        "artifact_version": validation["artifact_version"],
        "plan": make_plan(store, validation["artifact_version"]),
        "pending": None,
        "exchanged": [],
        "created": [],
        "rollback_databases": DATABASES,
    }
    save(path, record)
    try:
        record["status"] = "switching"
        save(path, record)
        for item in record["plan"]:
            assert_api_stopped(api_url)
            if position(store, item) != "before":
                raise ValueError("Activation inputs changed after preparation")
            if item["active_uuid"] is None:
                record["pending"] = {
                    "operation": "install_empty",
                    "active": item["active"],
                }
                save(path, record)
                if uuid(store, item["empty"]) != item["empty_uuid"]:
                    raise ValueError("Activation placeholder UUID changed")
                store.execute(f"RENAME TABLE {item['empty']} TO {item['active']}")
                record["created"].append(item["active"])
            record["pending"] = {"operation": "exchange", "active": item["active"]}
            save(path, record)
            store.execute(f"SYSTEM STOP MERGES {item['active']}")
            store.execute(f"SYSTEM STOP MERGES {item['candidate']}")
            store.execute(f"EXCHANGE TABLES {item['active']} AND {item['candidate']}")
            record["exchanged"].append([item["active"], item["candidate"]])
            record["pending"] = None
            save(path, record)
        completed(store, record)
        for item in record["plan"]:
            store.execute(f"SYSTEM START MERGES {item['active']}")
        record["status"] = "completed"
        save(path, record)
    except Exception:
        rollback(store, path, record)
        raise
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--api-url", default="http://127.0.0.1:8007")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    action = rollback_activation if args.rollback else activate
    print(
        json.dumps(action(CapacityStore(), args.root, args.api_url), ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
