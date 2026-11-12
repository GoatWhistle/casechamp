from app.adapter.municipal.assignment import MunicipalSpatialIndex
from app.domain.normative.model import AccessRow
from app.usecase.municipalities import Municipality


def municipality(identifier: str, west: float, east: float) -> Municipality:
    return Municipality(
        identifier,
        "07000000",
        identifier,
        6,
        [[[(west, 44), (east, 44), (east, 45), (west, 45), (west, 44)]]],
        "https://source",
        "2026-11-11",
        "abc",
        "polygon",
        1,
    )


def row(identifier: str, longitude: float | None, latitude: float | None = 44.5) -> AccessRow:
    return AccessRow(identifier, identifier, None, latitude, longitude, None, None, None, "unknown")


def test_unique_owner_assignment_excludes_shared_boundaries_and_overlap() -> None:
    index = MunicipalSpatialIndex([municipality("a", 40, 41), municipality("b", 41, 42)])
    assigned = index.assign(
        [row("a", 40.5), row("b", 41.5), row("border", 41), row("out", 45), row("missing", None)]
    )
    assert [item.id for item in assigned.rows["a"]] == ["a"]
    assert [item.id for item in assigned.rows["b"]] == ["b"]
    assert assigned.assigned == 2
    assert assigned.ambiguous == 1
    assert assigned.outside == 1
    assert assigned.coordinates_missing == 1
    overlap = MunicipalSpatialIndex([municipality("a", 40, 42), municipality("b", 41, 43)])
    assert overlap.assign([row("overlap", 41.5)]).ambiguous == 1


def test_actual_polygon_holes_and_dateline_copies_remain_separate() -> None:
    boundary = municipality("east", 170, 191)
    index = MunicipalSpatialIndex([boundary])
    assigned = index.assign([row("wrapped", -175), row("normal", 179), row("out", 0)])
    assert assigned.assigned == 2
    assert assigned.ambiguous == 0
