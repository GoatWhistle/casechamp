from dataclasses import asdict, replace

import pyarrow as pa
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.normative.model import Facility
from app.repository.clickhouse.normative_schema import SCHEMAS


def test_source_hash_survives_the_facility_snapshot_and_stays_optional_for_old_inputs() -> None:
    original = replace(facility(), source_sha256="ab" * 32)
    values = pa.Table.from_pylist(
        [{"run_id": "run", **asdict(original)}], schema=SCHEMAS["run_facilities"]
    ).to_pylist()[0]
    assert values.pop("run_id") == "run"
    assert Facility(**values) == original
    assert facility().source_sha256 is None


def test_coordinate_snapshot_round_trips_separately_from_the_address_document() -> None:
    original = replace(
        facility(),
        source_sha256="ab" * 32,
        coordinate_snapshot_sha256="cd" * 32,
        coordinate_snapshot_url="https://example.org/extract.osm.pbf",
    )
    values = pa.Table.from_pylist(
        [{"run_id": "run", **asdict(original)}], schema=SCHEMAS["run_facilities"]
    ).to_pylist()[0]
    values.pop("run_id")
    assert Facility(**values) == original
    assert facility().coordinate_snapshot_sha256 is None
