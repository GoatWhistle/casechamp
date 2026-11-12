import type { Map as LibreMap } from "maplibre-gl"
import { expect, it, vi } from "vitest"
import {
  fitNationalView,
  HOME_PADDING,
  resizeMapView,
} from "@/entities/region/osm-map/camera/national-view"

const bounds = [19, 41, 191, 82] as const
function mapAt(longitude = 105, zoom = 2) {
  return {
    isMoving: () => false,
    cameraForBounds: vi.fn(() => ({ center: { lng: 105, lat: 67 }, zoom: 2 })),
    getCenter: () => ({ lng: longitude, lat: 67 }),
    getZoom: () => zoom,
    fitBounds: vi.fn(),
    resize: vi.fn(),
    redraw: vi.fn(),
    setMinZoom: vi.fn(),
  }
}

it("uses one equal padding for national reset and viewport changes", () => {
  const map = mapAt()
  fitNationalView(map as unknown as LibreMap, bounds, 0)
  expect(map.fitBounds).toHaveBeenLastCalledWith(
    [
      [19, 41],
      [191, 82],
    ],
    { padding: HOME_PADDING, duration: 0, maxZoom: 18 },
  )
  expect(resizeMapView(map as unknown as LibreMap, bounds, true)).toBe(true)
  expect(map.resize).toHaveBeenCalledOnce()
  expect(map.setMinZoom).toHaveBeenCalledWith(0)
  expect(map.fitBounds).toHaveBeenCalledTimes(2)
})

it("preserves a user panned or zoomed view during resize", () => {
  for (const map of [mapAt(100), mapAt(105, 3)]) {
    expect(resizeMapView(map as unknown as LibreMap, bounds, true)).toBe(false)
    expect(map.resize).toHaveBeenCalledOnce()
    expect(map.fitBounds).not.toHaveBeenCalled()
  }
})
