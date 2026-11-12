import type { Map as LibreMap } from "maplibre-gl"
import { expect, it, vi } from "vitest"
import { focusCluster } from "@/entities/region/osm-map/normative-layer/normative-cluster-focus"
import { normalizedViewport } from "@/entities/region/osm-map/normative-layer/use-normative-viewport"

it("preserves antimeridian viewports and clamps world copies and zoom", () => {
  expect(normalizedViewport(170, -95, 190, 95, 5.9)).toEqual({
    west: 170,
    east: -170,
    south: -90,
    north: 90,
    zoom: 5,
  })
  expect(normalizedViewport(-220, -80, 220, 80, 24)).toEqual({
    west: -180,
    east: 180,
    south: -80,
    north: 80,
    zoom: 20,
  })
})

it("interrupts an existing movement and opens a cluster instantly with reduced motion", () => {
  const stop = vi.fn()
  const fitBounds = vi.fn()
  const map = { stop, fitBounds, getZoom: () => 17 } as unknown as LibreMap
  expect(focusCluster(map, { count: 25, bounds: "[37,55,38,56]" }, true)).toBe(true)
  expect(stop).toHaveBeenCalledOnce()
  expect(fitBounds).toHaveBeenCalledWith(
    [
      [37, 55],
      [38, 56],
    ],
    {
      padding: 96,
      maxZoom: 18,
      duration: 0,
    },
  )
  expect(stop.mock.invocationCallOrder[0]).toBeLessThan(fitBounds.mock.invocationCallOrder[0] ?? 0)
})

it("leaves an individual origin selectable and ignores malformed cluster bounds", () => {
  const stop = vi.fn()
  const map = { stop } as unknown as LibreMap
  expect(focusCluster(map, { count: 1, bounds: "[37,55,38,56]" }, true)).toBe(false)
  expect(focusCluster(map, { count: 2, bounds: "[37,null,38,56]" }, true)).toBe(false)
  expect(focusCluster(map, { count: 2, bounds: "broken" }, true)).toBe(false)
  expect(stop).not.toHaveBeenCalled()
})
