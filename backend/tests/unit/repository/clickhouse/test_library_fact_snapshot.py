from dataclasses import asdict

import pyarrow as pa
from pyarrow import ipc
from tests.unit.domain.normative.library.factories import INSTANT, facts

from app.domain.normative.library.facts import LibraryFacts
from app.repository.clickhouse.normative_schema import SCHEMAS


def test_library_snapshot_preserves_nulls_flags_inventory_and_validity() -> None:
    original = facts()
    schema = SCHEMAS["run_library_facts"]
    table = pa.Table.from_pylist([{"run_id": "run", **asdict(original)}], schema=schema)
    buffer = pa.BufferOutputStream()
    with ipc.new_stream(buffer, schema) as stream:
        stream.write_table(table)
    restored = ipc.open_stream(buffer.getvalue()).read_all().to_pylist()[0]
    assert restored.pop("run_id") == "run"
    for key in ("eligible_facility_ids", "verified_closed_way_ids"):
        restored[key] = tuple(restored[key])
    assert LibraryFacts(**restored) == original
    assert restored["service_eligible"] is True
    assert restored["scenario_verified"] is False


def test_decision_time_is_nullable_for_old_runs_and_separate_from_storage_time() -> None:
    schema = pa.schema([SCHEMAS["runs"].field("qualification_as_of")])
    table = pa.Table.from_pylist(
        [
            {"qualification_as_of": INSTANT},
            {"qualification_as_of": None},
        ],
        schema=schema,
    )
    assert table.to_pylist() == [
        {"qualification_as_of": INSTANT},
        {"qualification_as_of": None},
    ]
