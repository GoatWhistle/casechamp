from pathlib import Path
from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.municipal_cache_revision import MunicipalCacheRevision


def test_published_baseline_invalidates_cache_without_changing_database(tmp_path: Path) -> None:
    reader = Mock()
    reader.rows.return_value = [{'name': 'part', 'rows': 1}]
    revision = MunicipalCacheRevision(reader, tmp_path / 'indices', tmp_path / 'baselines')
    before = revision()
    path = tmp_path / 'baselines' / 'new'
    path.mkdir(parents=True)
    (path / 'sha256').write_text('new-baseline')
    assert revision() != before


def test_database_change_refuses_to_reuse_loaded_sources(tmp_path: Path) -> None:
    reader = Mock()
    reader.rows.return_value = [{'name': 'part', 'rows': 1}]
    revision = MunicipalCacheRevision(reader, tmp_path, tmp_path)
    revision()
    reader.rows.return_value = [{'name': 'replacement', 'rows': 1}]
    with pytest.raises(DataUnavailable, match='reload'):
        revision()
    assert MunicipalCacheRevision(reader, tmp_path, tmp_path)()
