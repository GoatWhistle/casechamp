import math

import pytest

from app.domain.municipal_metrics import MunicipalObservation, aggregate_metric, municipal_contains


def point(
    identifier: str, population: int | None, value: float | None, rural: bool = True
) -> MunicipalObservation:
    return MunicipalObservation(
        identifier, 40, 44, population, {"hansen_idx": value, "rai_2km": value}, rural
    )


def test_weighted_hansen_uses_only_finite_measurements_and_exposes_coverage() -> None:
    result = aggregate_metric(
        [
            point("a", 100, 10),
            point("b", 300, 30),
            point("c", 100, None),
            point("d", 100, math.nan),
        ],
        "hansen_idx",
        "index_points",
    )
    assert result.value == 25
    assert result.population == 600
    assert result.measured_population == 400
    assert result.population_coverage == pytest.approx(2 / 3)
    assert aggregate_metric([point("zero", 10, 0)], "hansen_idx", "index_points").value == 0


def test_missing_population_is_unavailable_and_rural_rai_excludes_urban_denominator() -> None:
    assert aggregate_metric([point("a", None, 10)], "hansen_idx", "index_points").value is None
    result = aggregate_metric([point("r", 100, 1), point("u", 900, 0, False)], "rai_2km", "ratio")
    assert result.value == 1
    assert result.population == 100


def test_original_polygon_holes_and_antimeridian_are_respected() -> None:
    polygon: list[list[list[tuple[float, float]]]] = [
        [
            [(170, 50), (-170, 50), (-170, 70), (170, 70), (170, 50)],
            [(175, 55), (178, 55), (178, 58), (175, 58), (175, 55)],
        ]
    ]
    assert municipal_contains(-175, 60, polygon)
    assert not municipal_contains(176, 56, polygon)
    assert not municipal_contains(0, 60, polygon)
