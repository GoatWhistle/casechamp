from dataclasses import replace
from datetime import UTC, datetime
from typing import cast
from unittest.mock import Mock

from app.domain.normative.index import IndexBasis
from app.usecase.normative.index_map import (
    IndexMapInput,
    IndexMapQueries,
    IndexMapRepository,
    IndexSummary,
)


def row() -> IndexMapInput:
    basis = IndexBasis(
        "N01",
        "RU",
        "132n",
        "2",
        "2016-02-27",
        "https://example.org",
        "minutes",
        (60,),
        "a" * 64,
        "unconfirmed",
    )
    summary = IndexSummary(
        "R",
        "N01",
        "run",
        "2026-11-12",
        "a" * 64,
        "minutes",
        "reference_points",
        60,
        60,
        80,
        80,
        70,
        70,
        10,
        9,
        1,
    )
    return IndexMapInput("R", "Region", basis, "run", summary)


def test_changed_measurement_and_changed_basis_cannot_keep_stale_map_values() -> None:
    source = row()
    assert source.basis is not None
    assert source.summary is not None
    repository = Mock(spec=IndexMapRepository)
    repository.inputs.return_value = [
        replace(source, run_id="new"),
        replace(source, basis=replace(source.basis, definition_sha256="b" * 64)),
    ]
    values = IndexMapQueries(
        cast(IndexMapRepository, repository), lambda: datetime.now(UTC)
    ).regions("N01")
    assert all(value.status == "unpublished" and value.value_min is None for value in values)


def test_baseline_scenario_and_absent_population_are_distinct() -> None:
    source = row()
    assert source.basis is not None
    assert source.summary is not None
    repository = Mock(spec=IndexMapRepository)
    repository.inputs.return_value = [source]
    queries = IndexMapQueries(cast(IndexMapRepository, repository), lambda: datetime.now(UTC))
    assert queries.regions("N01", "baseline")[0].value_min == 80
    assert queries.regions("N01", "scenario")[0].value_min == 70
    repository.inputs.return_value = [
        replace(
            source,
            basis=replace(source.basis, criterion_id="N05"),
            summary=replace(
                source.summary,
                criterion_id="N05",
                scenario_min=None,
                scenario_max=None,
                weighting="population",
            ),
        )
    ]
    value = queries.regions("N05")[0]
    assert value.status == "population_unknown"
    assert value.value_min is None


def test_a_summary_with_outdated_weighting_is_not_shown_as_current() -> None:
    source = row()
    assert source.summary is not None
    repository = Mock(spec=IndexMapRepository)
    repository.inputs.return_value = [
        replace(source, summary=replace(source.summary, weighting="population"))
    ]
    value = IndexMapQueries(cast(IndexMapRepository, repository), lambda: datetime.now(UTC))
    assert value.regions("N01")[0].status == "unpublished"
