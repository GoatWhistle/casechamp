from dataclasses import asdict, replace
from unittest.mock import Mock

from tests.unit.domain.normative.fire_evidence.factories import facility

from app.repository.clickhouse.regional_catalog import ClickHouseRegionalCatalogRepository


def test_batched_catalog_preserves_official_empty_and_directory_precedence() -> None:
    reader = Mock()
    base = {'id': 'shared', 'name': 'Inventory', 'address': '', 'latitude': 44., 'longitude': 43.,
            'source_url': 'https://example.org/pin', 'snapshot_url': 'https://example.org/snapshot',
            'source_sha256': 'a' * 64, 'observed_at': '2026-11-13'}
    directory = replace(facility(), id='shared', service='medical', name='Directory')
    official = replace(directory, id='official', name='Official')
    reader.rows.side_effect = [
        [{'id': 'A'}, {'id': 'B'}, {'id': 'C'}],
        [{**base, 'region_id': region} for region in ['A', 'B', 'C', 'outside']],
        [{**asdict(directory), 'membership_region': region} for region in ['A', 'B', 'C']],
    ]
    repository = ClickHouseRegionalCatalogRepository(reader)
    repository.service_directories = Mock()
    repository.service_directories.latest_by_region.return_value = {'A': [], 'B': [official]}
    result = repository.routing_candidates('medical')
    assert result == [directory, official]
    assert reader.rows.call_count == 3
