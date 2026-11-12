import gzip
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl" / "analytics"))
import export_snapshot as snapshot


class Source:
    def __init__(self, counts=None):
        self.counts = iter(counts or [2] * 20)
        self.sql = []
        self.url = urlsplit("http://localhost:8123")
        self.headers = {"X-ClickHouse-User": "test"}

    def rows(self, sql):
        self.sql.append(sql)
        if sql.startswith("SELECT count()"):
            return [{"n": next(self.counts)}]
        return [
            {
                "statement": "CREATE TABLE `plexus_graph`.`nodes` (id UInt64) ENGINE = MergeTree ORDER BY id"
            }
        ]


@pytest.fixture(autouse=True)
def enough_space(monkeypatch):
    monkeypatch.setattr(
        snapshot.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )


def test_exports_restore_manifest_and_verifies_resume_without_reexport(
    tmp_path, monkeypatch
):
    calls = []

    def stream(client, table, path):
        calls.append(table)
        with gzip.open(path, "wb") as output:
            output.write(b"native transport fixture")

    monkeypatch.setattr(snapshot, "stream_native", stream)
    client = Source()
    result = snapshot.export_snapshot(client, tmp_path, ["plexus_graph.nodes"])
    entry = result["tables"][0]
    assert {
        "table",
        "asset",
        "bytes",
        "sha256",
        "rows",
        "schema",
        "staging",
    } <= entry.keys()
    assert entry["rows"] == 2 and entry["staging"] is False
    assert entry["schema"].startswith("CREATE TABLE plexus_graph.nodes")
    assert json.loads((tmp_path / "manifest.json").read_text()) == result
    assert snapshot.export_snapshot(client, tmp_path, ["plexus_graph.nodes"]) == result
    assert calls == ["plexus_graph.nodes"]
    assert all(
        sql.startswith(("SELECT count()", "SHOW CREATE TABLE")) for sql in client.sql
    )
    path = tmp_path / entry["asset"]
    path.write_bytes(path.read_bytes()[:-1] + b"x")
    with pytest.raises(RuntimeError, match="integrity"):
        snapshot.export_snapshot(client, tmp_path, ["plexus_graph.nodes"])


def test_changed_source_never_publishes_partial_asset_or_manifest(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        snapshot,
        "stream_native",
        lambda client, table, path: path.write_bytes(b"partial"),
    )
    with pytest.raises(RuntimeError, match="changed while"):
        snapshot.export_snapshot(Source([2, 3]), tmp_path, ["plexus_graph.nodes"])
    assert list(tmp_path.iterdir()) == []


def test_requires_fifteen_gib_before_any_database_read(tmp_path, monkeypatch):
    monkeypatch.setattr(
        snapshot.shutil,
        "disk_usage",
        lambda _: SimpleNamespace(free=snapshot.MIN_FREE_BYTES - 1),
    )
    client = Source()
    with pytest.raises(RuntimeError, match="15 GiB"):
        snapshot.export_snapshot(client, tmp_path, ["plexus_graph.nodes"])
    assert client.sql == []


def test_table_identifiers_reject_sql_and_path_injection(tmp_path):
    client = Source()
    with pytest.raises(ValueError):
        snapshot.export_snapshot(
            client, tmp_path, ["plexus_graph.nodes; DROP DATABASE plexus_graph"]
        )
    assert client.sql == []


def test_native_transport_reads_bounded_chunks_and_compresses_on_disk(
    tmp_path, monkeypatch
):
    payload = b"native" * (snapshot.CHUNK_BYTES // 2)
    reads = []

    class Response:
        status = 200
        offset = 0

        def getheader(self, name):
            return None

        def read(self, size):
            reads.append(size)
            result = payload[self.offset : self.offset + size]
            self.offset += len(result)
            return result

    response = Response()
    connection = SimpleNamespace(
        request=lambda *args, **kwargs: None,
        getresponse=lambda: response,
        close=lambda: None,
    )
    monkeypatch.setattr(
        snapshot.http.client, "HTTPConnection", lambda *args, **kwargs: connection
    )
    path = tmp_path / "native.gz"
    snapshot.stream_native(Source(), "plexus_graph.nodes", path)
    assert gzip.decompress(path.read_bytes()) == payload
    assert len(reads) >= 3 and max(reads) == snapshot.CHUNK_BYTES


def test_native_http_success_with_embedded_exception_is_rejected(tmp_path, monkeypatch):
    pieces = iter(
        [
            b"native data\r\n__exception__\r\nrandom-tag\r\nCode: 1. DB::Exception: failed",
            b"",
        ]
    )
    response = SimpleNamespace(
        status=200, getheader=lambda name: "random-tag", read=lambda size: next(pieces)
    )
    connection = SimpleNamespace(
        request=lambda *args, **kwargs: None,
        getresponse=lambda: response,
        close=lambda: None,
    )
    monkeypatch.setattr(
        snapshot.http.client, "HTTPConnection", lambda *args, **kwargs: connection
    )
    with pytest.raises(RuntimeError, match="inside the Native stream"):
        snapshot.stream_native(Source(), "plexus_graph.nodes", tmp_path / "native.gz")


def test_legacy_error_is_detected_before_a_long_trailing_stack_evades_tail_check(
    tmp_path, monkeypatch
):
    pieces = iter([b"native\nCode: 42. DB::Exception: failure", b"x" * 65536, b""])
    response = SimpleNamespace(
        status=200, getheader=lambda name: None, read=lambda size: next(pieces)
    )
    connection = SimpleNamespace(
        request=lambda *args, **kwargs: None,
        getresponse=lambda: response,
        close=lambda: None,
    )
    monkeypatch.setattr(
        snapshot.http.client, "HTTPConnection", lambda *args, **kwargs: connection
    )
    with pytest.raises(RuntimeError, match="inside the Native stream"):
        snapshot.stream_native(Source(), "plexus_graph.nodes", tmp_path / "native.gz")
