import numpy as np
from federal_city_origins import apportion


def test_cell_population_sums_exactly_to_the_distributed_city_population() -> None:
    shares = apportion(12_365_610, np.array([3.0, 1.0, 1.0, 2.0]))
    assert int(shares.sum()) == 12_365_610
    assert shares[0] > shares[3] > shares[1]


def test_rounding_remainder_goes_to_the_largest_fractional_shares() -> None:
    assert apportion(10, np.array([1.0, 1.0, 1.0])).tolist() == [4, 3, 3]
