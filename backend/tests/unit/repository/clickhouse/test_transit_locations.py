from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.transit_locations import ClickHouseTransitLocations


def test_settlement_origin_retains_saved_coordinates_and_reference_status() -> None:
    reader = Mock()
    reader.rows.side_effect = [[], [{'id': 'place', 'name': 'Village', 'latitude': 44.0, 'longitude': 43.0}]]
    result = ClickHouseTransitLocations(reader).origin('R', 'place', 'walk-revision')
    assert (result.latitude, result.longitude) == (44.0, 43.0)
    assert result.coordinate_status == 'settlement_reference_not_entrance'
    sql, parameters = reader.rows.call_args.args
    assert parameters == {'region': 'R', 'id': 'place'}
    assert 'graph_revision' in sql and 'regional_origin_snapshots' in sql


def test_unknown_origin_does_not_fabricate_a_location() -> None:
    reader = Mock()
    reader.rows.return_value = []
    with pytest.raises(DataUnavailable):
        ClickHouseTransitLocations(reader).origin('R', 'missing', 'revision')


def test_residential_origin_does_not_fall_back_to_settlement() -> None:
    reader = Mock()
    reader.rows.return_value = [{'id': 'home', 'name': '', 'latitude': 44.1, 'longitude': 43.1}]
    result = ClickHouseTransitLocations(reader).origin('R', 'home', 'revision')
    assert result.coordinate_status == 'residential_reference_not_entrance'
    assert reader.rows.call_count == 1
