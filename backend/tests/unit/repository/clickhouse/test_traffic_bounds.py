from app.repository.clickhouse.traffic_source import validate_bounds


def test_multiregion_window_is_not_rejected_by_distance() -> None:
    bounds = [19.0, 41.0, 180.0, 82.0]
    assert validate_bounds(bounds) == bounds


def test_local_window_remains_available() -> None:
    bounds = [41.7, 44.44, 42.2, 44.81]
    assert validate_bounds(bounds) == bounds
