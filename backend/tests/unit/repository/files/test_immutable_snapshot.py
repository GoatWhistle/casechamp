from pathlib import Path

import pytest

from app.repository.files.immutable_snapshot import write_immutable


def test_repeated_publication_preserves_original_index_bytes(tmp_path: Path) -> None:
    path = tmp_path / 'snapshot.json'
    write_immutable(path, b'{"index": 42}')
    initial = path.stat().st_mtime_ns
    write_immutable(path, b'{"index": 42}')
    assert path.stat().st_mtime_ns == initial
    with pytest.raises(ValueError, match='immutable'):
        write_immutable(path, b'{"index": 24}')
    assert path.read_bytes() == b'{"index": 42}'
