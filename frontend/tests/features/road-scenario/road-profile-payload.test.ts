import { describe, expect, it } from "vitest"
import { profilePayload } from "@/features/road-scenario/profile/road-profile-payload"
import { scenarioPayload } from "@/features/road-scenario/scenario-payload"

const empty = { lanes: "", action: "lanes" as const }

describe("road capacity and closure payload", () => {
  it("supplies lane count without changing travel speed", () => {
    expect(profilePayload({ ...empty, lanes: "4" })).toEqual({ closed: false, lanes_total: 4 })
    expect(profilePayload(empty)).toBeNull()
    const result = scenarioPayload({
      regionId: "42",
      scenario: "road",
      wayIds: [101],
      profile: { closed: false, lanes_total: 4 },
      links: [],
    })
    expect(result?.changes).toEqual([{ way_id: 101, closed: false, lanes_total: 4 }])
  })
  it("rejects zero, fractional and unbounded lane counts", () => {
    for (const lanes of ["0", "-1", "3.5", "33", "Infinity"])
      expect(profilePayload({ ...empty, lanes })).toBeNull()
  })
  it("uses explicit closure and reopening actions", () => {
    expect(profilePayload({ ...empty, action: "closure" })).toEqual({ closed: true })
    expect(profilePayload({ ...empty, action: "opening" })).toEqual({ closed: false })
  })
})
