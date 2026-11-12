from dataclasses import replace

import pytest

from app.domain.normative.comparison import compare_routes
from app.domain.normative.model import AccessRow


def row(key: str, cost: float | None) -> AccessRow:
    return AccessRow(key, key, None, 55, 65, None, None, None, "unknown", distance_metres=cost)


def test_physical_comparison_does_not_need_or_invent_population() -> None:
    before = [row("up", 100), row("same", 200), row("lost", 400), row("missing", None)]
    after = [row("up", 250), row("same", 200), row("lost", None), row("missing", None)]
    result = compare_routes(before, after, "metres")
    assert result.paired_paths == 2 and result.increased == 1 and result.unchanged == 1
    assert result.lost == 1 and result.unresolved == 1
    assert result.mean_change == 75 and result.max_increase == 150


def test_missing_paths_are_distinct_from_a_measured_zero_change() -> None:
    missing = compare_routes([row("a", None)], [row("a", None)], "metres")
    same = compare_routes([row("a", 0)], [row("a", 0)], "metres")
    assert missing.mean_change is None and missing.unchanged == 0
    assert same.mean_change == 0 and same.unchanged == 1


def test_time_comparison_uses_minutes_and_reports_improvements_without_suppression() -> None:
    old = replace(row("a", 500), minutes=40)
    new = replace(row("a", 500), minutes=20)
    result = compare_routes([old], [new], "minutes")
    assert result.mean_change == -20 and result.decreased == 1


def test_incompatible_origin_sets_are_rejected() -> None:
    with pytest.raises(ValueError):
        compare_routes([row("a", 100)], [row("b", 200)], "metres")
