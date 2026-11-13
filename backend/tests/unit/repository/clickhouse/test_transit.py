import json
from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.transit import ClickHouseTransitCatalog


def head() -> dict[str, object]:
    return {'id': 'published', 'source_date': '2026-11-05', 'source_url': 'source', 'input_sha256': 'sha',
            'stop_count': 1, 'connection_count': 0, 'metadata': json.dumps({'clock_basis': 'source_clock',
            'timezone_verified': False, 'coverage_complete': False, 'operating_service_verified': False})}


def stop() -> dict[str, object]:
    return {'id': 'A', 'name': 'Stop', 'region_id': 'R', 'region_code': '26', 'latitude': None,
            'longitude': None, 'coordinate_status': 'unresolved', 'coordinate_source_url': '',
            'coordinate_source_sha256': ''}


def test_reader_exposes_only_published_snapshot_and_preserves_unknowns() -> None:
    reader = Mock()
    reader.rows.side_effect = [[head()], [stop()], [], [head()]]
    catalog = ClickHouseTransitCatalog(reader)
    result = catalog.latest()
    assert result.stops[0].latitude is None
    assert result.coverage_complete is False and result.timezone_verified is False
    assert catalog.latest() is result
    assert reader.rows.call_count == 4


def test_incomplete_snapshot_is_not_cached_or_returned() -> None:
    reader = Mock()
    reader.rows.side_effect = [[head()], [], []]
    catalog = ClickHouseTransitCatalog(reader)
    with pytest.raises(DataUnavailable, match='incomplete'):
        catalog.latest()
    assert catalog.cached is None


def test_absent_publication_is_not_an_empty_success() -> None:
    reader = Mock()
    reader.rows.return_value = []
    with pytest.raises(DataUnavailable, match='published'):
        ClickHouseTransitCatalog(reader).latest()
