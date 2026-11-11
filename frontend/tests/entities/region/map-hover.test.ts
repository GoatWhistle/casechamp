import type { Map as LibreMap } from "maplibre-gl"
import { afterEach, expect, it, vi } from "vitest"
import { bindHover } from "@/entities/region/osm-map/map-hover"
import { FILL_LAYER } from "@/entities/region/osm-map/osm-style"

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

it("coalesces pointer bursts into one region hit test and removes pending work", () => {
  vi.useFakeTimers()
  const setHover = vi.fn()
  let frame: FrameRequestCallback | undefined
  vi.stubGlobal("matchMedia", () => ({ matches: true }))
  vi.stubGlobal("requestAnimationFrame", (next: FrameRequestCallback) => {
    frame = next
    return 1
  })
  const cancel = vi.fn()
  vi.stubGlobal("cancelAnimationFrame", cancel)
  const handlers = new Map<string, (...args: unknown[]) => void>()
  const canvas = { addEventListener: vi.fn(), removeEventListener: vi.fn() }
  const map = {
    on: vi.fn((event, callback) => handlers.set(event, callback)),
    off: vi.fn(),
    getCanvas: () => canvas,
    getLayer: () => ({}),
    isMoving: () => false,
    queryRenderedFeatures: vi.fn(() => [{ id: 7, layer: { id: FILL_LAYER } }]),
  }
  const airportHover = vi.fn()
  const report = vi.fn()
  const dispose = bindHover(
    map as unknown as LibreMap,
    setHover,
    report,
    () => "region",
    airportHover,
    80,
  )
  for (let index = 0; index < 120; index++) {
    const handler = handlers.get("mousemove")
    expect(typeof handler).toBe("function")
    handler?.({ point: { x: index, y: 10 }, originalEvent: { clientX: index, clientY: 10 } })
  }
  expect(map.queryRenderedFeatures).not.toHaveBeenCalled()
  frame?.(0)
  expect(map.queryRenderedFeatures).toHaveBeenCalledTimes(1)
  expect(setHover).not.toHaveBeenCalled()
  vi.advanceTimersByTime(80)
  expect(setHover).toHaveBeenLastCalledWith(7)
  expect(report).toHaveBeenLastCalledWith("region", 119, 10)
  expect(airportHover).toHaveBeenLastCalledWith(undefined)
  handlers.get("mousemove")?.({ point: { x: 1, y: 2 }, originalEvent: { clientX: 1, clientY: 2 } })
  expect(typeof dispose).toBe("function")
  dispose?.()
  expect(cancel).toHaveBeenCalled()
  expect(canvas.removeEventListener).toHaveBeenCalled()
})
