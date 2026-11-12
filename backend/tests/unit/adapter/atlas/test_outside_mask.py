from shapely.geometry import MultiPolygon, Point, Polygon

from app.adapter.atlas.outside_mask import AtlasOutsideMask
from app.usecase.dto import BoundaryShape


def test_mask_wraps_actual_antimeridian_geometry_and_preserves_holes() -> None:
    ring = [(170.0, 50.0), (191.0, 50.0), (191.0, 70.0), (170.0, 70.0), (170.0, 50.0)]
    hole = [(175.0, 55.0), (178.0, 55.0), (178.0, 58.0), (175.0, 58.0), (175.0, 55.0)]
    boundaries = [BoundaryShape("east", "East", (170.0, 50.0, 191.0, 70.0), [[ring, hole]])]
    result = AtlasOutsideMask()(boundaries)
    mask = MultiPolygon([Polygon(rings[0], rings[1:]) for rings in result])
    assert not mask.covers(Point(179, 60))
    assert not mask.covers(Point(-175, 60))
    assert mask.covers(Point(176, 56))
    assert mask.covers(Point(0, 60))
    assert mask.is_valid
