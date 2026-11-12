import json
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.usecase.test_index_map import row

from app.adapter.normative.archived_indices import ArchivedIndexMapRepository
from app.domain.errors import DataUnavailable
from app.usecase.normative.index_map import IndexMapArchive, IndexMapQueries, IndexMapRepository
from app.usecase.normative.index_map_models import IndexMapRegion
from app.usecase.normative.scenario_indices import ScenarioIndexRepository

REPORT = Path(__file__).resolve().parents[4] / "docs/results/normative-live-index-coverage.json"


def test_storage_unavailable_returns_exact_archived_scenario_aggregates_with_provenance() -> None:
    repository = Mock(spec=IndexMapRepository)
    repository.inputs.side_effect = DataUnavailable("Missing measurements")
    archive = ArchivedIndexMapRepository(REPORT)
    result = IndexMapQueries(
        cast(IndexMapRepository, repository), lambda: datetime.now(UTC), archive=archive
    ).regions("N01")
    report = json.loads(REPORT.read_text())
    saved = report["results"][0]["rows"]
    assert len(result) == len(saved) == 84
    assert [
        (
            value.region_id,
            value.value_min,
            value.value_max,
            value.status,
            value.run_id,
            value.measured_at,
        )
        for value in result
    ] == [
        (
            value["region_id"],
            value["value_min"],
            value["value_max"],
            value["status"],
            value["run_id"],
            value["measured_at"],
        )
        for value in saved
    ]
    assert all(
        value.data_source == "archived_aggregate" and not value.detail_available for value in result
    )
    assert all(
        value.source_report_sha256 == sha256(REPORT.read_bytes()).hexdigest()
        and value.source_checked_at == report["checked_at"]
        for value in result
    )
    assert not any(value.legal_compliance_confirmed for value in result)


def test_live_unavailable_never_uses_scenario_archive_for_baseline() -> None:
    repository, archive = Mock(spec=IndexMapRepository), Mock(spec=IndexMapArchive)
    repository.inputs.side_effect = DataUnavailable("Missing measurements")
    queries = IndexMapQueries(
        cast(IndexMapRepository, repository),
        lambda: datetime.now(UTC),
        archive=cast(IndexMapArchive, archive),
    )
    with pytest.raises(DataUnavailable):
        queries.regions("N01", "baseline")
    archive.regions.assert_not_called()


def test_only_missing_live_aggregates_are_filled_and_current_numeric_values_win() -> None:
    source = row()
    repository, archive = Mock(spec=IndexMapRepository), Mock(spec=IndexMapArchive)
    repository.inputs.return_value = [
        source,
        replace(source, region_id="missing", region_name="Missing", run_id=None, summary=None),
    ]
    archived = IndexMapRegion(
        "missing",
        "Archived name",
        31,
        42,
        "reference_points",
        "scenario_ready",
        "archived-run",
        "2026-11-12",
        60,
        60,
        "minutes",
        10,
        9,
        data_source="archived_aggregate",
        detail_available=False,
    )
    archive.regions.return_value = [archived]
    queries = IndexMapQueries(
        cast(IndexMapRepository, repository),
        lambda: datetime.now(UTC),
        archive=cast(IndexMapArchive, archive),
    )
    result = queries.regions("N01")
    assert result[0].value_min == 70 and result[0].data_source == "live"
    assert result[1] is archived
    assert len(result) == 2


def test_missing_comparison_models_do_not_discard_a_live_numeric_index() -> None:
    repository, models, archive = (
        Mock(spec=IndexMapRepository),
        Mock(spec=ScenarioIndexRepository),
        Mock(spec=IndexMapArchive),
    )
    repository.inputs.return_value = [row()]
    models.regions.side_effect = DataUnavailable("No comparison snapshots")
    result = IndexMapQueries(
        cast(IndexMapRepository, repository),
        lambda: datetime.now(UTC),
        cast(ScenarioIndexRepository, models),
        cast(IndexMapArchive, archive),
    ).regions("N01")
    assert result[0].value_min == 70 and result[0].data_source == "live"
    archive.regions.assert_not_called()


def test_unregulated_live_status_is_not_overridden_by_an_old_archive() -> None:
    source = row()
    assert source.basis is not None
    repository, archive = Mock(spec=IndexMapRepository), Mock(spec=IndexMapArchive)
    repository.inputs.return_value = [
        replace(source, basis=replace(source.basis, regulation="not_regulated"))
    ]
    result = IndexMapQueries(
        cast(IndexMapRepository, repository),
        lambda: datetime.now(UTC),
        archive=cast(IndexMapArchive, archive),
    ).regions("N01")
    assert result[0].status == "not_regulated" and result[0].value_min is None
    archive.regions.assert_not_called()


def test_report_never_invents_missing_thresholds_or_legal_confirmation() -> None:
    archive = ArchivedIndexMapRepository(REPORT)
    rows = archive.regions("N08", "scenario")
    assert len(rows) == 84
    assert sum(value.value_min is None for value in rows) == 2
    assert all(
        value.data_source == "archived_aggregate" and not value.detail_available for value in rows
    )
    with pytest.raises(DataUnavailable, match="scenario aggregates only"):
        archive.regions("N08", "baseline")
