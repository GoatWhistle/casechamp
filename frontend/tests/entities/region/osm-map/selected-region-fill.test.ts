import type { Map as LibreMap } from "maplibre-gl"
import { expect, it, vi } from "vitest"
import { buildBoundaryAtlas } from "@/entities/region/osm-map/boundary-geojson"
import { revealSelectedRegions } from "@/entities/region/osm-map/camera/region-fill"

it("reveals the selected region's original map and restores shading when selection clears", () => {
  const atlas = buildBoundaryAtlas([
    { id: "01000000", name: "One", bounds: [1, 1, 2, 2], polygons: [] },
    { id: "02000000", name: "Two", bounds: [2, 2, 3, 3], polygons: [] },
  ])
  const map = { setFeatureState: vi.fn() }
  revealSelectedRegions(map as unknown as LibreMap, atlas, ["01000000"])
  expect(map.setFeatureState).toHaveBeenCalledWith(
    { source: "regions", id: 1000000 },
    { selected: true },
  )
  expect(map.setFeatureState).toHaveBeenCalledWith(
    { source: "regions", id: 2000000 },
    { selected: false },
  )
  map.setFeatureState.mockClear()
  revealSelectedRegions(map as unknown as LibreMap, atlas, [])
  expect(map.setFeatureState).toHaveBeenCalledTimes(2)
  expect(map.setFeatureState.mock.calls.every(([, state]) => state.selected === false)).toBe(true)
})
