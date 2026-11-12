from dataclasses import asdict, replace

import pyarrow as pa
from tests.unit.domain.normative.library.factories import INSTANT
from tests.unit.domain.normative.medical.factories import criterion, facility, facts, row

from app.domain.normative.medical.qualification import apply_medical_evidence
from app.domain.normative.model import AccessRow
from app.repository.clickhouse.normative_schema import SCHEMAS


def test_qualified_row_preserves_selected_threshold_and_both_primary_sources() -> None:
    evidence = replace(facts(), threshold_minutes=45)
    result = apply_medical_evidence(
        criterion(),
        [replace(row(), minutes=46, state="exceeded")],
        [evidence],
        [facility()],
        "network",
        INSTANT,
        [],
    )[0]
    schema = SCHEMAS["run_rows"]
    records = pa.Table.from_pylist(
        [
            {"run_id": "run", "stage": "scenario", **asdict(result)},
        ],
        schema=schema,
    ).to_pylist()
    restored = records[0]
    assert restored.pop("run_id") == "run"
    assert restored.pop("stage") == "scenario"
    restored["uncertainty"] = tuple(restored["uncertainty"])
    assert AccessRow(**restored) == result
    assert restored["threshold_minutes"] == 45
    assert restored["catchment_source_url"] == evidence.catchment_source_url
    assert restored["threshold_source_url"] == evidence.regional_adjustment_source_url
    assert restored["population"] == 100
    assert restored["state"] == "exceeded"
