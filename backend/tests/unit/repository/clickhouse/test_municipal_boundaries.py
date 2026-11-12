import json
from typing import cast

import pytest

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.municipalities import ClickHouseMunicipalRepository


class Reader:
    def __init__(self, geometry_type: str = "MultiPolygon") -> None:
        self.geometry_type = geometry_type

    def rows(self, sql: str, parameters: dict[str, str]) -> list[dict[str, object]]:
        assert " FINAL " in sql
        assert parameters == {"region": "07000000"}
        return [
            {
                "id": "osm-relation-1",
                "region_id": "07000000",
                "name": "Source name",
                "admin_level": 6,
                "geometry_json": json.dumps(
                    {
                        "type": self.geometry_type,
                        "coordinates": [[[[40, 44], [41, 44], [41, 45], [40, 44]]]],
                    }
                ),
                "source_url": "https://www.openstreetmap.org/relation/1",
                "observed_at": "2026-11-11",
                "source_sha256": "abc",
                "region_assignment": "polygon_overlap",
                "region_overlap_fraction": 0.99,
            }
        ]


def test_persisted_geometry_is_read_without_replacement() -> None:
    repository = ClickHouseMunicipalRepository(cast(ClickHouseReader, Reader()))
    result = repository.boundaries("07000000")
    assert tuple(result[0].coordinates[0][0][0]) == (40, 44)
    assert result[0].region_overlap_fraction == 0.99


def test_wrong_geometry_type_is_not_invented() -> None:
    repository = ClickHouseMunicipalRepository(cast(ClickHouseReader, Reader("Polygon")))
    with pytest.raises(DataUnavailable):
        repository.boundaries("07000000")
