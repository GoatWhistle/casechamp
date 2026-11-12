from pathlib import Path

from synthetic_traffic.model import Zone
from tests.unit.adapter.traffic.test_calculation import snapshot

from app.adapter.traffic.focus import resolve_focus
from app.usecase.traffic import TrafficJob, TrafficScope


def test_named_city_focus_uses_stored_housing_and_preserves_explicit_selection(
    tmp_path: Path,
) -> None:
    snapshot(tmp_path)
    settlements = [Zone("a", 0, 100, 44, 42), Zone("b", 2, 100, 44, 42.1)]
    homes = [
        Zone("home-1", 0, 50, 44.001, 42.001),
        Zone("home-2", 0, 50, 44.002, 42.002),
        Zone("home-3", 2, 100, 44, 42.1),
    ]
    job = TrafficJob("traffic-focus", TrafficScope(places=["A"], objective="congestion"))
    resolved, evidence = resolve_focus(job, tmp_path, settlements, homes)
    assert len(resolved.scope.focus_bounds) == 4
    assert evidence["buildings"] == 2
    assert evidence["administrative_boundary"] is False
    same, _ = resolve_focus(resolved, tmp_path, settlements, homes)
    assert same == resolved
