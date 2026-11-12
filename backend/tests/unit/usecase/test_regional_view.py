import pytest

from app.domain.errors import InvalidQuery
from app.usecase.normative.regional_view import RegionalMapBounds, validate_page


@pytest.mark.parametrize(
    "bounds",
    [
        RegionalMapBounds(181, 0, 0, 10),
        RegionalMapBounds(0, 10, 1, 0),
        RegionalMapBounds(float("nan"), 0, 10, 1),
    ],
)
def test_invalid_view_bounds_fail_before_storage(bounds: RegionalMapBounds) -> None:
    with pytest.raises(InvalidQuery):
        bounds.validate()


@pytest.mark.parametrize("page,size", [(0, 50), (2147483648, 50), (1, 101)])
def test_unbounded_page_requests_are_rejected(page: int, size: int) -> None:
    with pytest.raises(InvalidQuery):
        validate_page(page, size, "")
