import type { Map as LibreMap } from "maplibre-gl"
import { afterEach, expect, it, vi } from "vitest"
import { observeMapResize } from "@/entities/region/osm-map/camera/national-view"

const bounds = [19, 41, 191, 82] as const
const observers: (() => void)[] = []

class FakeResizeObserver {
  constructor(callback: () => void) {
    observers.push(callback)
  }
  observe() {
    return undefined
  }
  disconnect() {
    return undefined
  }
}

function zoomedMap() {
  return {
    isMoving: () => false,
    cameraForBounds: vi.fn(() => ({ center: { lng: 105, lat: 67 }, zoom: 2 })),
    getCenter: () => ({ lng: 56, lat: 59 }),
    getZoom: () => 6,
    fitBounds: vi.fn(),
    resize: vi.fn(),
    redraw: vi.fn(),
    setMinZoom: vi.fn(),
    panBy: vi.fn(),
  }
}

afterEach(() => {
  observers.length = 0
  vi.unstubAllGlobals()
})

it("keeps the top edge of a zoomed map in place when a phone sheet opens or closes", () => {
  vi.stubGlobal("ResizeObserver", FakeResizeObserver)
  const map = zoomedMap()
  const element = { clientWidth: 390, clientHeight: 844 } as HTMLElement
  observeMapResize(map as unknown as LibreMap, element, () => bounds, { current: true })
  Object.assign(element, { clientHeight: 371 })
  observers[0]?.()
  expect(map.panBy).toHaveBeenLastCalledWith([0, -236.5], { animate: false })
  Object.assign(element, { clientHeight: 844 })
  observers[0]?.()
  expect(map.panBy).toHaveBeenLastCalledWith([0, 236.5], { animate: false })
})

it("does not pan when only the national view is refitted", () => {
  vi.stubGlobal("ResizeObserver", FakeResizeObserver)
  const map = { ...zoomedMap(), getCenter: () => ({ lng: 105, lat: 67 }), getZoom: () => 2 }
  const element = { clientWidth: 390, clientHeight: 844 } as HTMLElement
  observeMapResize(map as unknown as LibreMap, element, () => bounds, { current: true })
  Object.assign(element, { clientHeight: 371 })
  observers[0]?.()
  expect(map.panBy).not.toHaveBeenCalled()
  expect(map.fitBounds).toHaveBeenCalledOnce()
})
