from dataclasses import replace

import pytest

from app.domain.normative.index import IndexBasis, IndexThresholdInterval, index_values
from app.domain.normative.model import AccessRow


def basis() -> IndexBasis:
    return IndexBasis(
        "N01",
        "RU",
        "132n",
        "2",
        "2016-02-27",
        "https://example.org/act",
        "minutes",
        (60,),
        "a" * 64,
        "unconfirmed",
    )


def test_missing_medical_population_does_not_become_a_population_coverage_percentage() -> None:
    rows = [
        AccessRow("one", "One", None, 55, 65, "f", 30, None, "unknown"),
        AccessRow("two", "Two", None, 55, 65, None, None, None, "unknown"),
    ]
    result = index_values(rows, basis())[0]
    assert result.point_share_percent == 50
    assert result.unresolved_points == 1
    assert result.population_share_percent is None
    assert result.population is None


def test_known_population_is_weighted_and_threshold_boundary_is_inclusive() -> None:
    rows = [
        AccessRow("one", "One", 900, 55, 65, "f", 60, None, "unknown"),
        AccessRow("two", "Two", 100, 55, 65, "f", 61, None, "unknown"),
    ]
    result = index_values(rows, basis())[0]
    assert result.point_share_percent == 50
    assert result.population_share_percent == 90
    assert result.within_population == 900


def test_contextual_thresholds_remain_separate_instead_of_selecting_a_legal_condition() -> None:
    rows = [AccessRow("one", "One", None, 55, 65, "f", None, None, "unknown", distance_metres=700)]
    results = index_values(rows, replace(basis(), unit="metres", thresholds=(500, 800, 1000)))
    assert [result.point_share_percent for result in results] == [0, 100, 100]
    assert index_values([], basis())[0].point_share_percent is None


def test_duplicate_origins_cannot_inflate_the_index_denominator() -> None:
    row = AccessRow("one", "One", 1, 55, 65, "f", 30, None, "unknown")
    with pytest.raises(ValueError):
        index_values([row, row], basis())


def test_published_source_intervals_cannot_become_single_cutoffs() -> None:
    interval = IndexThresholdInterval(30, 40, "urban_okrug", "transport", "municipal_library")
    original = replace(
        basis(),
        required_mode="none",
        regulation="local_selection_required",
        thresholds=(),
        intervals=(interval,),
    )
    assert index_values([], original) == []
    with pytest.raises(ValueError):
        index_values([], replace(original, regulation="threshold", thresholds=(40,)))
    with pytest.raises(ValueError):
        index_values([], replace(original, intervals=(replace(interval, minimum=50),)))
