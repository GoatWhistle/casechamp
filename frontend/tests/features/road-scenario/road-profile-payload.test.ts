import { describe, expect, it } from "vitest"
import { profilePayload, speedFactor } from "@/features/road-scenario/profile/road-profile-payload"
import { scenarioPayload } from "@/features/road-scenario/scenario-payload"

const empty = { lanes: "", highway: "", surface: "", speed: "" }

describe("road profile scenario payload", () => {
  it("keeps unspecified source attributes and supplies total lane count", () => {
    expect(profilePayload({ ...empty, lanes: "4" })).toEqual({ lanes_total: 4 })
    expect(profilePayload(empty)).toBeNull()
  })

  it("rejects zero, fractional and unbounded lane counts", () => {
    for (const lanes of ["0", "-1", "3.5", "33", "Infinity"])
      expect(profilePayload({ ...empty, lanes })).toBeNull()
  })

  it("accepts explicit class, surface and comma decimal design speed", () => {
    expect(
      profilePayload({ ...empty, highway: "motorway", surface: "asphalt", speed: "90,5" }),
    ).toEqual({ highway: "motorway", surface: "asphalt", speed_kmh: 90.5 })
    expect(profilePayload({ ...empty, speed: "0" })).toBeNull()
  })

  it("does not combine a profile update with the old speed multiplier", () => {
    const result = scenarioPayload({
      regionId: "42",
      scenario: "road",
      wayIds: [101],
      speed: null,
      profile: { lanes_total: 4 },
      links: [],
    })
    expect(result?.changes).toEqual([{ way_id: 101, speed_factor: 1, lanes_total: 4 }])
  })

  it("keeps manual controls backward compatible", () => {
    expect(speedFactor("1,2")).toBe(1.2)
    expect(speedFactor("0")).toBe(0)
    expect(speedFactor("")).toBeNull()
    expect(speedFactor("4")).toBeNull()
  })
})
