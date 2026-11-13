import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable
from app.repository.files.municipal_read_cache import FileMunicipalReadCache
from app.usecase.municipal_read_cache import MunicipalReadCache


def test_cache_survives_restart_and_invalidates_revision_and_parameters(tmp_path: Path) -> None:
    revision = Mock(return_value='one')
    compute = Mock(return_value=json.dumps({'value': 42}))
    cache = MunicipalReadCache(FileMunicipalReadCache(tmp_path), revision)
    assert cache.read('roads', {'region': 'a'}, compute) == compute.return_value
    restarted = MunicipalReadCache(FileMunicipalReadCache(tmp_path), revision)
    assert restarted.read('roads', {'region': 'a'}, compute) == compute.return_value
    compute.assert_called_once()
    revision.return_value = 'two'
    restarted.read('roads', {'region': 'a'}, compute)
    restarted.read('roads', {'region': 'b'}, compute)
    assert compute.call_count == 3


def test_failures_and_results_from_changing_sources_are_not_cached(tmp_path: Path) -> None:
    revision = Mock(side_effect=['one', 'two'])
    cache = MunicipalReadCache(FileMunicipalReadCache(tmp_path), revision)
    assert cache.read('roads', {}, lambda: '{"ok":true}') == '{"ok":true}'
    assert list(tmp_path.glob('*.json')) == []
    cache = MunicipalReadCache(FileMunicipalReadCache(tmp_path), lambda: 'one')
    compute = Mock(side_effect=DataUnavailable('Missing source'))
    with pytest.raises(DataUnavailable):
        cache.read('roads', {}, compute)
    assert list(tmp_path.glob('*.json')) == []


def test_corrupt_cache_is_recomputed(tmp_path: Path) -> None:
    cache = MunicipalReadCache(FileMunicipalReadCache(tmp_path), lambda: 'one')
    compute = Mock(return_value='{"ok":true}')
    cache.read('roads', {}, compute)
    next(tmp_path.glob('*.json')).write_text('broken')
    assert cache.read('roads', {}, compute) == '{"ok":true}'
    assert compute.call_count == 2


def test_saved_municipality_does_not_wait_for_another_cold_calculation(tmp_path: Path) -> None:
    cache = MunicipalReadCache(FileMunicipalReadCache(tmp_path), lambda: 'one')
    cache.read('baseline', {'municipality': 'warm'}, lambda: '{"ready":true}')
    started, release = Event(), Event()

    def calculate() -> str:
        started.set()
        assert release.wait(5)
        return '{"cold":true}'

    with ThreadPoolExecutor(max_workers=2) as pool:
        cold = pool.submit(cache.read, 'baseline', {'municipality': 'cold'}, calculate)
        assert started.wait(2)
        warm = pool.submit(cache.read, 'baseline', {'municipality': 'warm'}, Mock())
        try:
            assert warm.result(timeout=.5) == '{"ready":true}'
        finally:
            release.set()
        cold.result(timeout=2)
