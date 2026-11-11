import json
import re


def save(path, record):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    temporary.replace(path)


def uuid(store, table):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*[.][A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("Unsupported activation table identifier")
    database, name = table.split(".")
    rows = store.rows(
        f"SELECT toString(uuid) uuid FROM system.tables WHERE database='{database}' AND name='{name}'"
    )
    if len(rows) > 1:
        raise ValueError("Activation table identity is ambiguous")
    return str(rows[0]["uuid"]) if rows else None


def position(store, item):
    active, candidate = uuid(store, item["active"]), uuid(store, item["candidate"])
    old, new = item["active_uuid"], item["candidate_uuid"]
    if old is not None:
        if (active, candidate) == (old, new):
            return "before"
        if (active, candidate) == (new, old):
            return "swapped"
    else:
        empty = item["empty_uuid"]
        if (active, candidate) == (None, new):
            return "before"
        if (active, candidate) == (empty, new):
            return "installed"
        if (active, candidate) == (new, empty):
            return "swapped"
    raise ValueError(
        f"Unexpected table UUIDs; inspect {item['active']} and {item['candidate']}"
    )


def verify_plan(record, tables, databases):
    expected = [
        (f"{database}.{name}", f"{databases[database]}.{name}")
        for database, names in tables.items()
        for name in names
    ]
    actual = [(item["active"], item["candidate"]) for item in record.get("plan", [])]
    if actual != expected:
        raise ValueError(
            "Activation journal has an unsupported or incomplete UUID plan"
        )
    for item in record["plan"]:
        if item["active_uuid"] is None:
            prefix = item["candidate"] + "__activation_empty_"
            if not item.get("empty", "").startswith(prefix) or not item.get(
                "empty_uuid"
            ):
                raise ValueError("Missing activation placeholder identity")


def rollback(store, path, record):
    for item in record["plan"]:
        position(store, item)
    record["status"] = "rolling_back"
    save(path, record)
    try:
        for item in reversed(record["plan"]):
            state = position(store, item)
            if state == "swapped":
                record["pending"] = {
                    "operation": "undo_exchange",
                    "active": item["active"],
                }
                save(path, record)
                store.execute(f"SYSTEM STOP MERGES {item['active']}")
                store.execute(f"SYSTEM STOP MERGES {item['candidate']}")
                store.execute(
                    f"EXCHANGE TABLES {item['active']} AND {item['candidate']}"
                )
            if item["active_uuid"] is None:
                if position(store, item) == "installed":
                    record["pending"] = {
                        "operation": "remove_empty",
                        "active": item["active"],
                    }
                    save(path, record)
                    store.execute(f"DROP TABLE {item['active']} SYNC")
                empty_uuid = uuid(store, item["empty"])
                if empty_uuid is not None:
                    if empty_uuid != item["empty_uuid"]:
                        raise ValueError("Activation placeholder UUID changed")
                    store.execute(f"DROP TABLE {item['empty']} SYNC")
            elif position(store, item) == "before":
                store.execute(f"SYSTEM START MERGES {item['active']}")
            record["pending"] = None
            save(path, record)
        record["status"] = "rolled_back"
        save(path, record)
    except Exception as error:
        record["status"] = "rollback_failed"
        record["rollback_error"] = str(error)
        save(path, record)
        raise
    return record
