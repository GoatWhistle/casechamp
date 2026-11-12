from dataclasses import asdict

import pyarrow as pa
from pyarrow import ipc
from tests.unit.domain.normative.test_walking_rules import facts

from app.domain.normative.walking_facts import WalkingFacts
from app.repository.clickhouse.normative_schema import SCHEMAS


def test_input_snapshot_preserves_typed_flags_nulls_and_zone_evidence() -> None:
    original = facts()
    schema = SCHEMAS["run_walking_facts"]
    table = pa.Table.from_pylist([{"run_id": "run", **asdict(original)}], schema=schema)
    buffer = pa.BufferOutputStream()
    with ipc.new_stream(buffer, schema) as stream:
        stream.write_table(table)
    restored = ipc.open_stream(buffer.getvalue()).read_all().to_pylist()[0]
    assert restored.pop("run_id") == "run"
    restored["zones"] = tuple(restored["zones"])
    restored["verified_closed_way_ids"] = tuple(restored["verified_closed_way_ids"])
    restored["eligible_facility_ids"] = tuple(restored["eligible_facility_ids"])
    assert WalkingFacts(**restored) == original
    assert restored["facts_verified"] is True
    assert restored["population"] is None
