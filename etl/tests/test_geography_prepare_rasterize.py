import json

import numpy as np
import pytest
from shapely.affinity import scale, translate
from shapely.geometry import MultiPolygon, Point, Polygon, box, mapping
from shapely.ops import unary_union
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.geography_prepare import prepare


def physical(geometry):
    return translate(
        scale(geometry, xfact=0.001, yfact=0.001, origin=(0, 0)), xoff=40, yoff=50
    )


def reference(features, water=False):
    combined = unary_union(features)
    result = np.zeros((7, 7), dtype=bool)
    for row, col in np.ndindex(result.shape):
        lon, lat = 40 + col * 0.001, 50 + row * 0.001
        cell = (
            Point(lon, lat)
            if water
            else box(lon - 0.0005, lat - 0.0005, lon + 0.0005, lat + 0.0005)
        )
        result[row, col] = combined.intersects(cell)
    return result


def prepared(tmp_path, layers):
    dem = tmp_path / "dem.npz"
    np.savez(
        dem,
        elevation_m=np.arange(49).reshape(7, 7),
        origin_lon=40,
        origin_lat=50,
        cell_degrees=0.001,
    )
    paths = []
    for name in ("water", "buildings", "protected"):
        path = tmp_path / (name + ".geojson")
        path.write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": mapping(value),
                            "properties": {},
                        }
                        for value in layers.get(name, [])
                    ],
                }
            )
        )
        paths.append(path)
    output = tmp_path / "geography.json"
    prepare(dem, *paths, output)
    return RasterGeography.load(output)


@pytest.mark.parametrize("layer", ["water", "buildings", "protected"])
@pytest.mark.parametrize(
    "geometry",
    [
        box(1.5, 1.5, 2.5, 2.5),
        box(1.9, 0.1, 2.1, 5.9),
        box(-0.6, -0.6, -0.5, -0.5),
        Polygon(
            [(0.5, 0.5), (5.5, 0.5), (5.5, 5.5), (0.5, 5.5)],
            holes=[[(1.5, 1.5), (4.5, 1.5), (4.5, 4.5), (1.5, 4.5)]],
        ),
        MultiPolygon([box(0.1, 4.1, 0.3, 4.3), box(3.2, 0.2, 3.4, 0.4)]),
    ],
)
def test_rasterized_masks_preserve_reference_intersections(tmp_path, layer, geometry):
    values = [physical(geometry)]
    result = prepared(tmp_path, {layer: values})
    expected = reference(values, water=layer == "water")
    actual = result.water if layer == "water" else result.blocked
    assert np.all(actual[expected])
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(result.elevation_m, np.arange(49).reshape(7, 7))


def test_many_overlapping_polygons_match_without_union(tmp_path):
    rng = np.random.default_rng(42)
    values = [
        physical(box(x, y, x + width, y + height))
        for x, y, width, height in rng.uniform(0.01, 2.8, (100, 4))
    ]
    result = prepared(tmp_path, {"buildings": values})
    np.testing.assert_array_equal(result.blocked, reference(values))


def test_empty_layers_preserve_clear_mask_and_source_paths(tmp_path):
    result = prepared(tmp_path, {})
    assert not result.blocked.any()
    assert not result.water.any()
    for layer in ("water", "buildings", "protected"):
        assert result.sources[layer] == str((tmp_path / (layer + ".geojson")).resolve())


def test_invalid_polygon_still_fails_instead_of_skipping(tmp_path):
    invalid = physical(Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)]))
    with pytest.raises(ValueError, match="valid polygons"):
        prepared(tmp_path, {"buildings": [invalid]})
