from unittest.mock import Mock

import pyarrow as pa
import pytest

from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Саратов", ["2"]),
        ("г. Саратов", ["2"]),
        ("г. Энгельс, Саратовская область", ["4"]),
        ("Энгельс, Саратовская область", ["4"]),
        ("Энгельс", ["3", "4"]),
        ("Энгельс, Алтайский край", []),
        ("Саратово", []),
    ],
)
def test_corridor_search_resolves_exact_names_and_region_qualifiers(
    query: str, expected: list[str]
) -> None:
    reader = Mock()
    reader.rows.return_value = [{"value": "test"}]
    reader.arrow.return_value = pa.table({
        "point_id": ["1", "2", "3", "4"],
        "settlement": ["село Саратовка", "г. Саратов", "посёлок Энгельс", "г. Энгельс"],
        "region": ["Алтайский край", "Саратовская область", "Оренбургская область", "Саратовская область"],
        "lon": [46., 46., 46., 46.],
        "lat": [51., 51., 51., 51.],
    })
    rows = ClickHouseGraphSnapshot(reader).read("corridor_places", {"query": query})
    assert [row[0] for row in rows] == expected
    assert "," not in reader.arrow.call_args.args[1]["pattern"]


def test_market_city_is_preferred_over_villages_with_the_same_name() -> None:
    reader = Mock()
    reader.rows.return_value = [{"value": "test"}]
    reader.arrow.side_effect = [
        pa.table({
            "point_id": ["1", "2"], "settlement": ["деревня Москва", "деревня Москва"],
            "region": ["Кировская область", "Тверская область"], "lon": [1., 2.], "lat": [1., 2.],
        }),
        pa.table({
            "oktmo_from": ["45000000000"], "city_from": ["Москва"], "region_from": ["Москва"],
            "lon_from": [37.6], "lat_from": [55.7],
        }),
    ]
    rows = ClickHouseGraphSnapshot(reader).read("corridor_places", {"query": "Москва"})
    assert [row[0] for row in rows] == ["45000000000"]
