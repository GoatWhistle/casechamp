from typing import Any, cast
from unittest.mock import Mock

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.index_map import ClickHouseIndexMapRepository


def test_index_inputs_use_exact_inventory_regions_without_synthesized_territories() -> None:
    reader = Mock(spec=ClickHouseReader)

    def rows(query: str, parameters: dict[str, object]) -> list[dict[str, Any]]:
        if "inventory_regions" in query:
            return [
                {"id": "07000000", "name": "First stored region"},
                {"id": "09000000", "name": "Second stored region"},
            ]
        return []

    reader.rows.side_effect = rows
    result = ClickHouseIndexMapRepository(cast(ClickHouseReader, reader)).inputs("N01")
    assert [(row.region_id, row.region_name) for row in result] == [
        ("07000000", "First stored region"),
        ("09000000", "Second stored region"),
    ]
    assert all(row.basis is None and row.summary is None and row.run_id is None for row in result)
