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
  expect(style.layers.find((layer) => layer.id === "base")).toMatchObject({
    paint: { "background-color": colors.outside },
  })
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

it("keeps contextual outlines outside the analytical region source", () => {
  const colors: OsmMapColors = {
    fills: ["#eee"],
    border: "#fff",
    selected: "#000",
    water: "#eee",
    outside: "#fff",
  }
  const data: FeatureCollection<MultiPolygon> = { type: "FeatureCollection", features: [] }
  const polygons = [
    [
      [
        [35, 46],
        [36, 46],
        [36, 47],
        [35, 47],
        [35, 46],
      ],
    ],
  ]
  const style = buildStyle(colors, data, 0, undefined, [
    { id: "context-one", name: "Context", bounds: [35, 46, 36, 47], polygons },
  ])
  expect(style.sources.regions).toMatchObject({ data })
  expect(style.sources["contextual-regions"]).toMatchObject({
    data: {
      features: [
        {
          properties: { display_only: true },
          geometry: { type: "MultiPolygon", coordinates: polygons },
        },
      ],
    },
  })
  expect(style.layers.find((layer) => layer.id === "contextual-region-border")).toMatchObject({
    type: "line",
    source: "contextual-regions",
  })
  expect(style.layers.find((layer) => layer.id === "osm-tiles")).toMatchObject({
    paint: { "raster-fade-duration": 0 },
  })
})

it("fills decorative regions uniformly and draws sourced water separately without index features", () => {
  const colors: OsmMapColors = {
    fills: ["#eee", "#fed", "#fca", "#e99"],
    border: "#fff",
    selected: "#000",
    water: "#abc",
    outside: "#fff",
  }
  const data: FeatureCollection<MultiPolygon> = { type: "FeatureCollection", features: [] }
  const shape = {
    id: "context",
    name: "Context",
    bounds: [1, 1, 2, 2],
    polygons: [
      [
        [
          [1, 1],
          [2, 1],
          [2, 2],
          [1, 2],
          [1, 1],
        ],
      ],
    ],
  }
  const style = buildStyle(colors, data, 0, undefined, [shape], [{ ...shape, id: "water" }])
  expect(style.layers.find((layer) => layer.id === "contextual-region-fill")).toMatchObject({
    paint: { "fill-color": "#e99", "fill-opacity": 0.72 },
  })
  expect(style.layers.find((layer) => layer.id === "contextual-water-fill")).toMatchObject({
    paint: { "fill-color": "#abc", "fill-opacity": 1 },
  })
  const ids = style.layers.map((layer) => layer.id)
  expect(ids.indexOf("contextual-water-fill")).toBeGreaterThan(
    ids.indexOf("contextual-region-fill"),
  )
  expect(ids.indexOf("contextual-water-fill")).toBeGreaterThan(ids.indexOf(FILL_LAYER))
  expect(style.sources.regions).toMatchObject({ data })
})
