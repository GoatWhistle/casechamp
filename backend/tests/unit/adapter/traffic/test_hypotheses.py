from pathlib import Path

import pytest
from synthetic_traffic.source import load_network
from tests.unit.adapter.traffic.test_calculation import snapshot

from app.adapter.traffic.hypotheses import resolve_hypotheses
from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficHypothesis


def test_grounded_place_hypotheses_map_to_stored_nodes_and_deduplicate(tmp_path: Path) -> None:
    snapshot(tmp_path)
    network = load_network(tmp_path)
    result = resolve_hypotheses([
        TrafficHypothesis("a", "b", "Bypass the measured detour"),
        TrafficHypothesis("B", "A", "Same corridor"),
    ], tmp_path, network)
    assert len(result) == 1
    assert (result[0]["source_node"], result[0]["target_node"]) == (10, 30)
    assert result[0]["origin"] == "agent_hypothesis"
    assert "geometry" not in result[0]


@pytest.mark.parametrize("source,target", [("imaginary", "b"), ("a", "A")])
def test_unresolved_or_identical_hypotheses_are_rejected(
    tmp_path: Path, source: str, target: str
) -> None:
    snapshot(tmp_path)
    with pytest.raises(InvalidQuery):
        resolve_hypotheses([TrafficHypothesis(source, target)], tmp_path, load_network(tmp_path))
