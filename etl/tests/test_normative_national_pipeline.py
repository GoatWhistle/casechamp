import io
from types import SimpleNamespace
from typing import ClassVar

import pytest
from synthetic_traffic.normative_national_pipeline import NationalPipeline


def test_disk_guard_accounts_for_incoming_source_and_preserves_stop_request(
    tmp_path, monkeypatch
):
    pipeline = NationalPipeline(tmp_path, 1)
    monkeypatch.setattr(
        "synthetic_traffic.normative_national_pipeline.shutil.disk_usage",
        lambda path: SimpleNamespace(free=2 * 1024**3),
    )
    with pytest.raises(RuntimeError, match="Disk guard"):
        pipeline.guard(2 * 1024**3)
    marker = pipeline.root / "STOP"
    marker.write_text("user-request")
    with pytest.raises(RuntimeError, match="Stop requested"):
        pipeline.guard()
    assert marker.read_text() == "user-request"


def test_truncated_source_does_not_enter_completed_manifest(tmp_path, monkeypatch):
    pipeline = NationalPipeline(tmp_path, 0)

    class Response(io.BytesIO):
        headers: ClassVar[dict[str, str]] = {"Content-Length": "10"}

    monkeypatch.setattr(
        "synthetic_traffic.normative_national_pipeline.urlopen",
        lambda *args, **kwargs: Response(b"short"),
    )
    with pytest.raises(ValueError, match="truncated"):
        pipeline.download("https://example.org/source", tmp_path / "source.part")
    assert not (pipeline.root / "osm/manifest.json").exists()
