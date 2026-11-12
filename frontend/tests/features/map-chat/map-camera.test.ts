import type { Map as LibreMap } from "maplibre-gl"
import { describe, expect, it, vi } from "vitest"
import { buildBoundaryAtlas } from "@/entities/region/osm-map/boundary-geojson"
import { aimCamera, regionFrame, settlementCenter } from "@/entities/region/osm-map/map-camera"
import { isChatMapCommand } from "@/shared/api/chat-map"

const atlas = buildBoundaryAtlas([
  { id: "01000000", name: "West", bounds: [85, 49, 91, 53], polygons: [] },
  { id: "02000000", name: "East", bounds: [170, 61, 191, 72], polygons: [] },
])

describe("map commands", () => {
  it("frames a group without wrapping eastern longitudes to the other side", () => {
    expect(regionFrame(atlas, ["01000000", "02000000"])).toEqual([85, 49, 191, 72])
    expect(regionFrame(atlas, ["02000000"])).toEqual([170, 61, 191, 72])
    expect(regionFrame(atlas, ["unknown"])).toBeNull()
  })
  it("rejects invalid event arguments before moving the map", () => {
    expect(isChatMapCommand({ action: "focus", region_ids: ["01000000"] })).toBe(true)
    expect(isChatMapCommand({ action: "focus", region_ids: [] })).toBe(false)
    expect(isChatMapCommand({ action: "focus", region_ids: ["invented"] })).toBe(false)
    expect(isChatMapCommand({ action: "reset", region_ids: ["01000000"] })).toBe(false)
    expect(isChatMapCommand({ action: "reset", region_ids: [] })).toBe(true)
  })
  it("validates settlement coordinates and preserves legacy commands", () => {
    const command = {
      action: "focus_settlement",
      region_ids: ["01000000"],
      settlement: { id: "one", name: "Town", region_id: "01000000", longitude: 42, latitude: 45 },
    }
    expect(isChatMapCommand(command)).toBe(true)
    expect(
      isChatMapCommand({ ...command, settlement: { ...command.settlement, latitude: 91 } }),
    ).toBe(false)
    expect(isChatMapCommand({ ...command, region_ids: ["02000000"] })).toBe(false)
    expect(isChatMapCommand({ ...command, settlement: null })).toBe(false)
  })
  it("focuses the stored point, interrupts earlier movement and honors instant motion", () => {
    const element = { dataset: {} }
    const map = {
      stop: vi.fn(),
      getLayer: vi.fn(),
      getSource: vi.fn(),
      setFilter: vi.fn(),
      setFeatureState: vi.fn(),
      getContainer: () => element,
      easeTo: vi.fn(),
    }
    const settlement = {
      id: "one",
      name: "Town",
      region_id: "01000000",
      longitude: 42,
      latitude: 45,
    }
    aimCamera(
      map as unknown as LibreMap,
      atlas,
      {
        action: "focus_settlement",
        region_ids: ["01000000"],
        settlement,
      },
      null,
      0,
      0,
    )
    expect(map.stop).toHaveBeenCalledOnce()
    expect(map.easeTo).toHaveBeenCalledWith(
      expect.objectContaining({ center: [42, 45], zoom: 12, duration: 0, essential: false }),
    )
    expect(settlementCenter({ ...settlement, longitude: -179 })).toEqual([181, 45])
  })
  it("validates road geometry before accepting a saved map command", () => {
    const command = {
      action: "focus_road",
      region_ids: [],
      road: {
        names: ["Lane"],
        length_km: 0.167,
        lines: [
          [
            [42, 45],
            [42.002, 45],
          ],
        ],
      },
    }
    expect(isChatMapCommand(command)).toBe(true)
    expect(isChatMapCommand({ ...command, road: { ...command.road, lines: [] } })).toBe(false)
    expect(isChatMapCommand({ ...command, road: { ...command.road, lines: [[[42, 45]]] } })).toBe(
      false,
    )
    expect(
      isChatMapCommand({
        ...command,
        road: {
          ...command.road,
          lines: [
            [
              [42, 45],
              [NaN, 45],
            ],
          ],
        },
      }),
    ).toBe(false)
  })
})
