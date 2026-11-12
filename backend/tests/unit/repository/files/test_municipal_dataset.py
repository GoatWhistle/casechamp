import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.domain.errors import DataUnavailable
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow
from app.repository.files.municipal_dataset import JsonMunicipalDataset
from app.repository.files.municipal_dataset_export import export_municipal_dataset
from app.usecase.municipal_dataset import (
    MunicipalSnapshotSource,
    aggregate_snapshot,
    persist_aggregation,
)
from app.usecase.municipalities import Municipality


def source(criterion: str = "N04", fire_speed: float = 40) -> MunicipalSnapshotSource:
    metadata = {
        "unit": "metres" if criterion == "N04" else "minutes",
        "mode": "walk" if criterion == "N04" else "emergency_response",
        "fire_profile": {"speed_kmh": fire_speed, "assumption": "Explicit scenario assumption"},
        "facilities": 2,
        "source_urls": ["https://source"],
    }
    return MunicipalSnapshotSource(
        "07000000",
        criterion,
        "real-run",
        "scenario",
        "2026-11-13",
        "graph",
        "model",
        "physical_only",
        MeasurementDefinition.SINGLE_REFERENCE_POINT,
        json.dumps(metadata, sort_keys=True),
    )


def municipality() -> Municipality:
    return Municipality(
        "osm-relation-1",
        "07000000",
        "Real",
        6,
        [[[(40, 44), (41, 44), (41, 45), (40, 45), (40, 44)]]],
        "https://boundary",
        "2026-11-11",
        "abc",
        "polygon",
        1,
    )


def rows() -> list[AccessRow]:
    return [
        AccessRow(
            "one", "One", None, 44.2, 40.2, "facility", 8, None, "unknown", distance_metres=300
        ),
        AccessRow(
            "two", "Two", None, 44.5, 40.5, "facility", 15, None, "unknown", distance_metres=900
        ),
        AccessRow(
            "outside", "Outside", None, 45.5, 42, "facility", 2, None, "unknown", distance_metres=50
        ),
    ]


def test_source_snapshot_and_municipal_values_survive_restart_and_resume(tmp_path: Path) -> None:
    dataset = JsonMunicipalDataset(tmp_path)
    digest = dataset.snapshot(source(), rows())
    assert dataset.snapshot(source(), list(reversed(rows()))) == digest
    value = persist_aggregation(dataset, digest, municipality())
    assert [entry.point_share_percent for entry in value.values] == [50, 50, 100]
    assert value.reference_points == 2
    assert not value.legal_compliance_confirmed
    restored = JsonMunicipalDataset(tmp_path)
    assert restored.find_run("07000000", "N04", "real-run", "scenario") == digest
    assert restored.rows(digest) == sorted(rows(), key=lambda row: row.id)
    assert restored.existing(digest, municipality(), "N04") == value
    assert (
        restored.existing(
            digest,
            replace(municipality(), coordinates=[[[(39, 44), (41, 44), (41, 45), (39, 44)]]]),
            "N04",
        )
        is None
    )
    dataset.publish_source(digest)
    manifest = export_municipal_dataset(tmp_path, tmp_path / "export.jsonl.gz")
    assert manifest["aggregates"] == 1
    assert manifest["source_snapshots"] == [digest]
    assert persist_aggregation(restored, digest, municipality()) == value


def test_corrupt_or_incomplete_point_snapshot_is_rejected(tmp_path: Path) -> None:
    dataset = JsonMunicipalDataset(tmp_path)
    digest = dataset.snapshot(source(), rows())
    (tmp_path / "sources" / digest / "measurements.jsonl.gz").write_bytes(b"broken")
    with pytest.raises(DataUnavailable):
        dataset.rows(digest)


def test_fire_reuses_imported_10_20_minutes_and_requires_matching_assumption() -> None:
    value, identifiers = aggregate_snapshot(source("N03"), rows(), municipality())
    assert value.thresholds == (10, 20)
    assert [entry.point_share_percent for entry in value.values] == [50, 100]
    assert identifiers == ["one", "two"]
    mismatch, _ = aggregate_snapshot(source("N03", 60), rows(), municipality())
    assert mismatch.value is None
    assert mismatch.reason == "municipal_measurement_policy_mismatch"


def test_primary_fire_index_uses_population_weighting_not_point_share() -> None:
    measured = [replace(rows()[0], population=100), replace(rows()[1], population=900)]
    value, _ = aggregate_snapshot(source("N03"), measured, municipality())
    assert value.value == 10
    assert value.values[0].point_share_percent == 50
    assert value.values[0].population_share_percent == 10


def test_export_contains_only_current_published_source_per_municipal_criterion(
    tmp_path: Path,
) -> None:
    dataset = JsonMunicipalDataset(tmp_path)
    first = dataset.snapshot(source(), rows())
    persist_aggregation(dataset, first, municipality())
    second = dataset.snapshot(replace(source(), run_id="new-run", measured_at="2026-11-14"), rows())
    persist_aggregation(dataset, second, municipality())
    dataset.publish_source(second)
    manifest = export_municipal_dataset(tmp_path, tmp_path / "export.jsonl.gz")
    assert manifest["aggregates"] == 1
    assert manifest["historical_versions_excluded"] == 1
    assert manifest["source_snapshots"] == [second]
    assert manifest["cross_municipality_sums_valid"] is False


def test_resnapshot_repairs_missing_run_pointer_after_manifest_publication(tmp_path: Path) -> None:
    dataset = JsonMunicipalDataset(tmp_path)
    digest = dataset.snapshot(source(), rows())
    for pointer in (tmp_path / "runs").glob("*.json"):
        pointer.unlink()
    assert dataset.find_run("07000000", "N04", "real-run", "scenario") is None
    assert dataset.snapshot(source(), rows()) == digest
    assert dataset.find_run("07000000", "N04", "real-run", "scenario") == digest


def test_resnapshot_does_not_repair_pointer_for_corrupt_existing_source(tmp_path: Path) -> None:
    dataset = JsonMunicipalDataset(tmp_path)
    digest = dataset.snapshot(source(), rows())
    for pointer in (tmp_path / "runs").glob("*.json"):
        pointer.unlink()
    manifest = tmp_path / "sources" / digest / "manifest.json"
    record = json.loads(manifest.read_bytes())
    record["source_sha256"] = "0" * 64
    manifest.write_text(json.dumps(record))
    with pytest.raises(DataUnavailable):
        dataset.snapshot(source(), rows())
    assert dataset.find_run("07000000", "N04", "real-run", "scenario") is None
