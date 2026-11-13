import { describe, expect, it } from "vitest"
import { isChatMapCommand } from "@/shared/api/chat-map"

const command = {
  action: "focus",
  region_ids: ["07000000"],
  transit: {
    region_id: "07000000",
    snapshot_id: "snapshot",
    geometry_status: "stops_only_not_route_geometry",
    points: [{ id: "home", name: "Home", role: "origin", latitude: 44, longitude: 43 }],
  },
}
describe("transit map replay", () => {
  it("accepts saved points and rejects invalid coordinates or a mismatched region", () => {
    expect(isChatMapCommand(command)).toBe(true)
    expect(
      isChatMapCommand({ ...command, transit: { ...command.transit, region_id: "03000000" } }),
    ).toBe(false)
    expect(
      isChatMapCommand({
        ...command,
        transit: { ...command.transit, points: [{ ...command.transit.points[0], latitude: NaN }] },
      }),
    ).toBe(false)
    expect(
      isChatMapCommand({
        ...command,
        transit: { ...command.transit, geometry_status: "real_route" },
      }),
    ).toBe(false)
  })
})
