import type { Map as LibreMap } from "maplibre-gl"
import { afterEach, expect, it, vi } from "vitest"
import { focusView, stressPoints } from "@/entities/region/osm-map/use-stress-layer"
import type { StressImpact } from "@/shared/api/road-stress"

afterEach(() => vi.unstubAllGlobals())

it("focuses closure geometry before route results are available", () => {
  vi.stubGlobal("document", { querySelector: () => null })
  const fitBounds = vi.fn()
  const map = {
    fitBounds,
    getContainer: () => ({ getBoundingClientRect: () => ({ left: 0, right: 1440, width: 1440 }) }),
  } as unknown as LibreMap
  focusView(
    map,
    {
      jobId: "closure",
      impacts: [],
      route: null,
      focus: 1,
      closed: [
        [
          [37, 55],
          [30, 60],
        ],
      ],
    },
    true,
  )
  expect(fitBounds).toHaveBeenCalledWith(
    [
      [30, 55],
      [37, 60],
    ],
    expect.objectContaining({ duration: 0 }),
  )
})

it("does not show cached settlement points in the closure view", () => {
  const point = { point: { id: "settlement" } } as StressImpact
  const view = { jobId: "closure", route: null, focus: 1, impacts: [point], showPoints: false }
  expect(stressPoints(view, [point]).size).toBe(0)
  expect(stressPoints({ ...view, showPoints: true }, [point]).size).toBe(1)
})
