import json
from pathlib import Path

MIGRATION = Path(__file__).with_name("schema.sql")


def insert(client, table, records):
    if not records:
        return
    body = (
        "\n".join(
            json.dumps(row, ensure_ascii=False, allow_nan=False) for row in records
        )
        + "\n"
    ).encode()
    client.request(
        "INSERT INTO plexus_accessibility." + table + " FORMAT JSONEachRow", body
    )


def publish(source, run, rows, frequencies):
    source.assert_unchanged()
    for command in MIGRATION.read_text().split(";"):
        if command.strip():
            source.client.request(command)
    exists = source.client.rows(
        "SELECT count() AS n FROM plexus_accessibility.runs WHERE run_id='"
        + run["run_id"]
        + "'"
    )
    if int(exists[0]["n"]):
        raise ValueError("Completed run already exists")
    insert(source.client, "results", [dict(row, run_id=run["run_id"]) for row in rows])
    insert(
        source.client,
        "frequencies",
        [dict(row, run_id=run["run_id"]) for row in frequencies],
    )
    count = source.client.rows(
        "SELECT count() AS n FROM plexus_accessibility.results WHERE run_id='"
        + run["run_id"]
        + "'"
    )
    if int(count[0]["n"]) != len(rows):
        raise ValueError("Persisted result count differs")
    source.assert_unchanged()
    insert(source.client, "runs", [run])
