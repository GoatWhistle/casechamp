import json
import re
from pathlib import Path
from typing import get_type_hints

from analytics.client import ClickHouse
from app.repository.clickhouse.records import sql_type
from app.usecase.road_graph import RoadJob

FIELDS = ("changes", "result", "appraisal_assumptions", "appraisal_result")


def canonical_type(value: str) -> str:
    return re.sub(r"\s+|`", "", value)


def fingerprint(client, table, types):
    values = ",".join(f"CAST(`{name}` AS {kind})" for name, kind in types.items())
    return client.rows(
        f"SELECT count() n,groupBitXor(cityHash64(id,{values})) checksum FROM {table} FINAL"
    )[0]


def migrate(client, database="plexus_state", table="road_jobs"):
    if not all(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", x) for x in [database, table]):
        raise ValueError("Unsupported state identifier")
    target = database + "." + table
    busy = client.rows(
        f"SELECT count() n FROM {target} FINAL WHERE status IN ('queued','running')"
    )[0]["n"]
    if int(busy):
        raise ValueError(
            "Wait for running and queued calculations before schema migration"
        )
    backup = target + "_before_capacity_v1"
    original = {
        r["name"]: r["type"]
        for r in client.rows("DESCRIBE TABLE " + target)
        if r["name"] in FIELDS
    }
    expected = get_type_hints(RoadJob)
    desired = {name: sql_type(expected[name]) for name in FIELDS}
    if {name: canonical_type(kind) for name, kind in original.items()} == {
        name: canonical_type(kind) for name, kind in desired.items()
    }:
        return {"status": "already_current", "table": target}
    if not client.rows("EXISTS TABLE " + backup)[0]["result"]:
        client.request(f"CREATE TABLE {backup} AS {target}")
        client.request(f"ALTER TABLE {backup} ATTACH PARTITION ALL FROM {target}")
    before = fingerprint(client, target, original)
    for name, kind in desired.items():
        if canonical_type(original.get(name, "")) != canonical_type(kind):
            client.request(f"ALTER TABLE {target} MODIFY COLUMN `{name}` {kind}")
    after = fingerprint(client, target, original)
    if before != after:
        raise ValueError(
            "Stored job legacy fields differ after capacity schema migration"
        )
    return {
        "status": "migrated",
        "table": target,
        "backup": backup,
        "before": before,
        "after": after,
        "old_types": original,
        "new_types": desired,
    }


def main():
    result = migrate(ClickHouse())
    output = Path("work/road-capacity/state-migration.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ["old_types", "new_types"]
            }
        )
    )


if __name__ == "__main__":
    main()
