import type { Map as LibreMap } from "maplibre-gl"
import { describe, expect, it, vi } from "vitest"
import { buildBoundaryAtlas } from "@/entities/region/osm-map/boundary-geojson"
import { aimCamera } from "@/entities/region/osm-map/map-camera"

const atlas = buildBoundaryAtlas([])

describe("road focus", () => {
  it("fits the exact section across the date line and redraws its highlight on replay", () => {
    const element = document.createElement("div")
    element.getBoundingClientRect = () => ({ width: 1440, height: 900 }) as DOMRect
    const setData = vi.fn()
    const map = {
      stop: vi.fn(),
      fitBounds: vi.fn(),
      getSource: () => ({ setData }),
      moveLayer: vi.fn(),
      getContainer: () => element,
    }
    const command = {
      action: "focus_road" as const,
      region_ids: [],
      road: {
        names: ["Lane"],
        length_km: 1,
        lines: [
          [
            [179.9, 65],
            [-179.9, 65],
          ],
        ],
      },
    }
    aimCamera(map as unknown as LibreMap, atlas, command, null, 0, 0)
    expect(map.stop).toHaveBeenCalledOnce()
    expect(map.fitBounds).toHaveBeenCalledWith(
      [
        [179.9, 65],
        [180.1, 65],
      ],
      expect.objectContaining({ maxZoom: 16, duration: 0, essential: false }),
    )
    expect(element.dataset.focusRoad).toBe("Lane")
    expect(setData).toHaveBeenCalledOnce()
    aimCamera(map as unknown as LibreMap, atlas, { ...command }, null, 0, 0)
    expect(map.fitBounds).toHaveBeenCalledTimes(2)
  })
})
