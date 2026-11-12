import { renderHook } from "@testing-library/react"
import type { Map as LibreMap, MapGeoJSONFeature } from "maplibre-gl"
import { expect, it, vi } from "vitest"
import { AIRPORT_MIN_ZOOM, useAirportLayer } from "@/entities/region/osm-map/use-airport-layer"
import type { AirportCatalog } from "@/shared/api/airports"
import { LocaleProvider } from "@/shared/i18n"

const popup = vi.hoisted(() => ({
  setLngLat: vi.fn().mockReturnThis(),
  setText: vi.fn().mockReturnThis(),
  addTo: vi.fn().mockReturnThis(),
  remove: vi.fn(),
}))
vi.mock("maplibre-gl", () => ({
  Popup: class {
    setLngLat = popup.setLngLat
    setText = popup.setText
    addTo = popup.addTo
    remove = popup.remove
  },
}))

it("hides airports at country zoom and removes an open popup when zooming out", () => {
  let zoom = 2
  const handlers = new Map<string, () => void>()
  const map = {
    getSource: () => null,
    addSource: vi.fn(),
    addLayer: vi.fn(),
    getContainer: () => document.createElement("div"),
    getZoom: () => zoom,
    on: vi.fn((event, layerOrHandler, handler) => handlers.set(event, handler ?? layerOrHandler)),
    off: vi.fn(),
  }
  const catalog: AirportCatalog = {
    airports: [
      {
        id: "1",
        name: "Airport",
        municipality: "Place",
        iata: "AAA",
        latitude: 45,
        longitude: 42,
        scheduled: true,
        kind: "small_airport",
      },
    ],
    assignments: [],
    source_url: "https://example.com",
    retrieved_at: "2026-11-12",
  }
  const { result, unmount } = renderHook(
    () => useAirportLayer({ current: map as unknown as LibreMap }, catalog, true),
    { wrapper: LocaleProvider },
  )
  expect(map.addLayer).toHaveBeenCalledWith(expect.objectContaining({ minzoom: AIRPORT_MIN_ZOOM }))
  const feature = {
    properties: { id: "1", name: "Airport", iata: "AAA" },
    geometry: { type: "Point", coordinates: [42, 45] },
  } as unknown as MapGeoJSONFeature
  result.current.current(feature)
  expect(popup.addTo).not.toHaveBeenCalled()
  zoom = 6
  result.current.current(feature)
  expect(popup.addTo).toHaveBeenCalledOnce()
  zoom = 4
  const removals = popup.remove.mock.calls.length
  handlers.get("zoom")?.()
  expect(popup.remove.mock.calls.length).toBeGreaterThan(removals)
  zoom = 6
  result.current.current(feature)
  expect(popup.addTo).toHaveBeenCalledTimes(2)
  unmount()
  expect(map.off).toHaveBeenCalledWith("zoom", expect.any(Function))
})
