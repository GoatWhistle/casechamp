from dataclasses import replace

import pytest
from tests.unit.usecase.test_atlas_usecases import FakeAtlas

from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.usecase.accessibility import (
    AccessibilityComparison,
    AccessibilityQueries,
    AccessibilityRow,
    AccessibilityRun,
    FrequencyCoverage,
)
from app.usecase.dto import RegionRecord


class StoredComparison:
    def __init__(self) -> None:
        run = AccessibilityRun(
            "run",
            "2026-11-10",
            "planned",
            "legacy",
            "snapshot",
            1000.0,
            "legacy_multimodal_road",
            82,
            180,
            155412,
            "incomplete",
            (),
        )
        rows = tuple(
            AccessibilityRow(season, 2, 10.0, 12.0, 2.0, 11.0, 12.0, 10.0, 100, 1.0)
            for season in ("summer", "winter")
        )
        self.value = AccessibilityComparison(
            "18000000", False, run, rows, (FrequencyCoverage("summer", "air", "trunk", 5, 0),)
        )

    def comparison(self, region_id: str, half_life: int) -> AccessibilityComparison:
        return self.value


def queries(repository: StoredComparison) -> AccessibilityQueries:
    atlas = FakeAtlas(region_rows=[RegionRecord("18000000", "Region", 1, 100)])
    return AccessibilityQueries(repository, atlas)


def test_incomplete_schedules_do_not_become_a_zero_index() -> None:
    result = queries(StoredComparison()).compare("18000000", 2)
    assert all(row.scheduled_index is None for row in result.rows)
    assert result.rows[0].potential == 12
    assert not result.source_current
    assert result.run.source_artifact == "snapshot"


def test_partial_season_pair_is_unavailable() -> None:
    repository = StoredComparison()
    repository.value = replace(repository.value, rows=repository.value.rows[:1])
    with pytest.raises(DataUnavailable):
        queries(repository).compare("18000000", 2)


def test_unsupported_half_life_and_unknown_region_are_rejected() -> None:
    query = queries(StoredComparison())
    with pytest.raises(InvalidQuery):
        query.compare("18000000", 3)
    with pytest.raises(RegionNotFound):
        query.compare("missing", 2)
