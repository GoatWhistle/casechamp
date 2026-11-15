import numpy as np
import rasterio
from rasterio.transform import from_origin
from synthetic_traffic import geography_tile
from synthetic_traffic.geography import RasterGeography


def test_glo30_integer_latitude_reads_sourced_southern_neighbor(tmp_path, monkeypatch):
    files = {}
    pixel = 1 / 3600
    for latitude in (43, 44):
        path = tmp_path / f"N{latitude}.tif"
        top = 44 + pixel / 2 if latitude == 43 else 44 + 10.5 * pixel
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=10,
            height=10,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(42 - pixel / 2, top, pixel, pixel),
        ) as output:
            output.write(np.full((10, 10), latitude, dtype=np.float32), 1)
        files[latitude] = path
    requested = []

    def dem(latitude, longitude, cache):
        requested.append((latitude, longitude))
        return files[latitude], {
            "url": f"test://N{latitude}E{longitude}",
            "sha256": "test fixture",
        }

    monkeypatch.setattr(geography_tile, "_dem", dem)
    monkeypatch.setattr(
        geography_tile,
        "_vectors",
        lambda *args: (
            {key: [] for key in ("water", "buildings", "protected")},
            {"provider": "test fixture"},
        ),
    )
    output = tmp_path / "tile"
    manifest = geography_tile.fetch_tile(
        [42, 44, 42.001, 44.001], output, tmp_path / "cache"
    )
    result = RasterGeography.load(output / "geography.npz")
    assert requested == [(43, 42), (44, 42)]
    np.testing.assert_array_equal(result.elevation_m[0], [43, 43])
    np.testing.assert_array_equal(result.elevation_m[1], [44, 44])
    assert (
        manifest["terrain_alignment"]["latitude_source_half_pixel_degrees"] == pixel / 2
    )
