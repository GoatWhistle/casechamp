import pytest

from app.domain.connectivity import PairAccess, group_score, pair_score
from app.domain.errors import InvalidQuery


@pytest.mark.parametrize(("hours", "expected"), [(0, 100), (2, 50), (4, 25), (8, 6.25)])
def test_fixed_time_scale(hours: float, expected: float) -> None:
    assert pair_score(PairAccess("reachable", hours)) == expected


def test_no_path_and_unknown_have_different_aggregation_semantics() -> None:
    connected = PairAccess("reachable", 2)
    assert group_score([connected, PairAccess("unreachable", None)]) == 25
    assert group_score([connected, PairAccess("unbound", None)]) is None


@pytest.mark.parametrize("hours", [None, -1, float("nan"), float("inf")])
def test_invalid_reachable_time_is_rejected(hours: float | None) -> None:
    with pytest.raises(InvalidQuery):
        pair_score(PairAccess("reachable", hours))
