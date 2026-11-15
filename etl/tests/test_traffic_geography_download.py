from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from synthetic_traffic import geography_fetch


class Response:
    def __init__(self, payload, declared):
        self.payload = payload
        self.headers = {} if declared is None else {"Content-Length": str(declared)}
        self.read_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        self.read_calls += 1
        return self.payload[:limit]


@pytest.mark.parametrize("declared", [3, None])
def test_complete_public_response_is_published(monkeypatch, declared):
    response = Response(b"abc", declared)
    monkeypatch.setattr(geography_fetch, "urlopen", lambda *args, **kwargs: response)
    with TemporaryDirectory() as directory:
        output = Path(directory) / "terrain.tif"
        result = geography_fetch.download("https://example.org/terrain.tif", output)
        assert output.read_bytes() == b"abc"
        assert result["bytes"] == 3


def test_truncated_body_never_receives_a_valid_cache_hash(monkeypatch):
    response = Response(b"abc", 40000000)
    monkeypatch.setattr(geography_fetch, "urlopen", lambda *args, **kwargs: response)
    with TemporaryDirectory() as directory:
        output = Path(directory) / "terrain.tif"
        with pytest.raises(ValueError, match="Incomplete public data response"):
            geography_fetch.download("https://example.org/terrain.tif", output)
        assert not output.exists()


def test_declared_oversized_body_fails_before_read(monkeypatch):
    response = Response(b"abc", 100000001)
    monkeypatch.setattr(geography_fetch, "urlopen", lambda *args, **kwargs: response)
    with TemporaryDirectory() as directory:
        output = Path(directory) / "terrain.tif"
        with pytest.raises(ValueError, match="oversized"):
            geography_fetch.download("https://example.org/terrain.tif", output)
        assert response.read_calls == 0
        assert not output.exists()
