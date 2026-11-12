from http.client import IncompleteRead
from io import BytesIO
from typing import cast
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request

import pytest

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader


@pytest.mark.parametrize("invalid", [0, -1, True, 1.5])
def test_read_limits_reject_invalid_values(invalid: object) -> None:
    with pytest.raises(ValueError):
        ClickHouseReader("http://example.org", "user", "secret", max_threads=cast(int, invalid))


class Response(BytesIO):
    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        self.headers: dict[str, str] = {}


def test_limits_are_request_scoped_and_keep_readonly_and_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = []

    def respond(request: Request, timeout: int) -> Response:
        observed.append(parse_qs(urlsplit(request.full_url).query))
        return Response(b'{"data": []}')

    monkeypatch.setattr("app.repository.clickhouse.client.urlopen", respond)
    bounded = ClickHouseReader(
        "http://example.org", "user", "secret", max_threads=1, max_block_size=8192
    )
    assert bounded.rows("SELECT {id:String}", {"id": "origin"}) == []
    ordinary = ClickHouseReader("http://example.org", "user", "secret")
    assert ordinary.rows("SELECT 1", {}) == []
    assert observed[0]["readonly"] == ["1"]
    assert observed[0]["param_id"] == ["origin"]
    assert observed[0]["max_threads"] == ["1"]
    assert observed[0]["max_block_size"] == ["8192"]
    assert "max_threads" not in observed[1]
    assert "max_block_size" not in observed[1]


class BrokenResponse(Response):
    def read(self, size: int | None = -1) -> bytes:
        raise IncompleteRead(b"partial", 100)


def test_truncated_storage_stream_is_an_explicit_unavailable_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def respond(request: Request, timeout: int) -> Response:
        return BrokenResponse(b"")

    monkeypatch.setattr("app.repository.clickhouse.client.urlopen", respond)
    reader = ClickHouseReader("http://example.org", "user", "secret")
    with pytest.raises(DataUnavailable) as result:
        reader.rows("SELECT 1", {})
    assert isinstance(result.value.__cause__, IncompleteRead)
