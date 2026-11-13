from pathlib import Path
from unittest.mock import Mock, patch

from app.adapter.traffic.municipal_baselines import MunicipalBaselines
from app.repository.files.municipal_read_cache import FileMunicipalReadCache
from app.usecase.municipal_read_cache import MunicipalReadCache
from app.usecase.municipal_scenarios import MunicipalTrafficBaseline
from app.usecase.traffic import TrafficJob, TrafficScope


def test_published_overlay_survives_restart_and_invalidates_with_sources(tmp_path: Path) -> None:
    revision = Mock(return_value="one")
    result = MunicipalTrafficBaseline("preview", "district", [], [], .5, None, "sha",
                                     TrafficJob("base", TrafficScope(), stage="preliminary"))
    first = MunicipalBaselines(tmp_path, Mock(), cache=MunicipalReadCache(
        FileMunicipalReadCache(tmp_path / "cache"), revision))
    with patch.object(first, "_get", return_value=result):
        assert first.get("region", "district") == result
    second = MunicipalBaselines(tmp_path, Mock(), cache=MunicipalReadCache(
        FileMunicipalReadCache(tmp_path / "cache"), revision))
    with patch.object(second, "_get", return_value=result) as compute:
        assert second.get("region", "district") == result
        compute.assert_not_called()
        revision.return_value = "two"
        assert second.get("region", "district") == result
        compute.assert_called_once()
