import { act, renderHook } from "@testing-library/react"
import type { MultiPolygon } from "geojson"
import type { Map as LibreMap } from "maplibre-gl"
import { expect, it, vi } from "vitest"
import {
  MUNICIPAL_FILL,
  municipalityBounds,
  useMunicipalityLayer,
} from "@/entities/region/osm-map/municipalities/use-municipality-layer"
import type { MunicipalityLayer } from "@/shared/api/municipalities"

const geometry: MultiPolygon = {
  type: "MultiPolygon",
  coordinates: [
    [
      [
        [40, 43],
        [41, 43],
        [41, 44],
        [40, 44],
        [40, 43],
      ],
    ],
  ],
}

it("uses supplied polygon bounds for a municipality", () => {
  expect(municipalityBounds(geometry)).toEqual([
    [40, 43],
    [41, 44],
  ])
  expect(municipalityBounds({ type: "MultiPolygon", coordinates: [] })).toBeNull()
})

it("selects a district on polygon click while leaving road clicks to the road layer", () => {
  let click: ((event: unknown) => void) | undefined
  const map = {
    getSource: vi.fn(() => null),
    addSource: vi.fn(),
    addLayer: vi.fn(),
    getLayer: vi.fn(() => ({})),
    getContainer: () => document.createElement("div"),
    setFilter: vi.fn(),
    fitBounds: vi.fn(),
    queryRenderedFeatures: vi.fn((): unknown[] => []),
    on: vi.fn((event, layer, callback) => {
      if (event === "click" && layer === MUNICIPAL_FILL) click = callback
    }),
    off: vi.fn(),
  }
  const onSelect = vi.fn()
  const layer: MunicipalityLayer = {
    collection: { type: "FeatureCollection", features: [] },
    selected: null,
    onSelect,
  }
  renderHook(() => useMunicipalityLayer({ current: map as unknown as LibreMap }, layer, true))
  act(() => click?.({ point: [0, 0], features: [{ properties: { id: "osm-relation-1" } }] }))
  expect(onSelect).toHaveBeenCalledWith("osm-relation-1")
  onSelect.mockClear()
  map.queryRenderedFeatures.mockReturnValue([{ layer: { id: "road-graph-lines" } }])
  act(() => click?.({ point: [0, 0], features: [{ properties: { id: "osm-relation-1" } }] }))
  expect(onSelect).not.toHaveBeenCalled()
})
