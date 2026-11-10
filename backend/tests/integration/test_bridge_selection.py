from pathlib import Path

from tests.storage import atlas_repository

from app.adapter.road_corridor.bridges import find_bridges
from app.adapter.road_graph.data import GraphData
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot


def test_saratov_and_pristannoe_bridge_selection_uses_actual_tagged_ways() -> None:
    data = GraphData(Path("unused"), ClickHouseGraphSnapshot(atlas_repository().reader))
    direct = find_bridges(data, "Саратов", 10, "Саратовский мост")
    bypass = find_bridges(data, "Пристанное, Саратовская область", 2, "")
    assert len(direct) == 1
    assert direct[0].corridor.way_ids == [203336910]
    crossing = next(c for c in bypass if c.corridor.way_ids == [27262951, 122013785])
    assert crossing.references == ["А-298"]
    assert len(crossing.corridor.lines) == 2
    assert 4.6 < crossing.corridor.length_km < 4.8
    selected = direct[0].corridor.way_ids + crossing.corridor.way_ids
    assert len(data.read("bridge_lengths", {"ids": selected})) == 3
