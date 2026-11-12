import type { FeatureCollection, MultiPolygon } from "geojson"
import { expect, it } from "vitest"
import { buildStyle, FILL_LAYER, type OsmMapColors } from "@/entities/region/osm-map/osm-style"

it("covers the raster outside supplied regions while retaining region interaction layers", () => {
  const colors: OsmMapColors = {
    fills: ["#fff"],
    border: "#000",
    selected: "#00f",
    water: "#eee",
    outside: "#fff",
  }
  const regions: FeatureCollection<MultiPolygon> = { type: "FeatureCollection", features: [] }
  const mask: MultiPolygon = {
    type: "MultiPolygon",
    coordinates: [
      [
        [
          [0, 0],
          [5, 0],
          [5, 5],
          [0, 5],
          [0, 0],
        ],
      ],
    ],
  }
  const style = buildStyle(colors, regions, 0, mask)
  const ids = style.layers.map((layer) => layer.id)
  expect(ids.indexOf("outside-regions-mask")).toBeGreaterThan(ids.indexOf("osm-tiles"))
  expect(ids.indexOf("outside-regions-mask")).toBeLessThan(ids.indexOf(FILL_LAYER))
  const layer = style.layers.find((value) => value.id === "outside-regions-mask")
  expect(layer).toMatchObject({ type: "fill", paint: { "fill-color": "#fff", "fill-opacity": 1 } })
  expect(style.sources["outside-regions"]).toMatchObject({
    type: "geojson",
    data: { geometry: mask },
    tolerance: 0,
  })
})
