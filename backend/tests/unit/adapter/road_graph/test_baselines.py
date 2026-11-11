from pathlib import Path

from app.adapter.road_graph.baselines import BaselineCache


def test_road_cost_model_namespaces_baseline_without_corrupting_json_revision(tmp_path: Path) -> None:
    revision = '{"artifact":"new-weights","base":["original-snapshot"]}'
    legacy = BaselineCache(tmp_path, revision)
    capacity = BaselineCache(tmp_path, revision, "road-capacity-v1")
    legacy.write("region", "road", 100)
    assert capacity.read("region", "road") is None
    capacity.write("region", "road", 98)
    assert capacity.read("region", "road") == 98
    assert legacy.read("region", "road") == 100
    assert BaselineCache(tmp_path, revision, "road-capacity-v2").read("region", "road") is None
