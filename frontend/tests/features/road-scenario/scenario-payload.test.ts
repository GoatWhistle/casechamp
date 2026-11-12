import { describe, expect, it } from "vitest"
import {
  additionOf,
  airportClosure,
  LINK_LIMIT,
  rejectionMessage,
  removalOf,
  scenarioPayload,
  toggleLink,
} from "@/features/road-scenario/scenario-payload"
import { ApiError } from "@/shared/api"
import type { LinkChangeInput } from "@/shared/api/road-graph"

const ferry = {
  network: "local",
  mode: "ferry",
  source: "98614486101",
  source_name: "Village",
  target: "98626101001",
  target_name: "Town",
  hours: 30.8,
  region: "Region",
}

describe("road scenario payload", () => {
  it("builds a links-only payload without road changes", () => {
    const links = [airportClosure(" Surgut ")]
    expect(scenarioPayload({ regionId: "71800000", scenario: "road", wayIds: [], links })).toEqual({
      region_id: "71800000",
      scenario: "road",
      changes: [],
      links: [
        { action: "remove", network: "intercity", mode: "air", source: "Surgut", target: "*" },
      ],
    })
  })

  it("combines selected roads with link changes", () => {
    const rail = additionOf("rail", "Moscow", "Tver", "1,5")
    expect(typeof rail).toBe("object")
    const payload = scenarioPayload({
      regionId: "28000000",
      scenario: "summer",
      wayIds: [7, 8],
      profile: { closed: true },
      links: [rail as LinkChangeInput],
    })
    expect(payload?.changes).toEqual([
      { way_id: 7, closed: true },
      { way_id: 8, closed: true },
    ])
    expect(payload?.links).toEqual([
      {
        action: "add",
        network: "intercity",
        mode: "rail",
        source: "Moscow",
        target: "Tver",
        hours: 1.5,
      },
    ])
  })

  it("refuses empty, invalid and seasonless local requests", () => {
    const local = removalOf(ferry)
    expect(local).toEqual({
      action: "remove",
      network: "local",
      mode: "ferry",
      source: "98614486101",
      target: "98626101001",
    })
    const base = { regionId: "98000000", wayIds: [] as number[] }
    expect(scenarioPayload({ ...base, scenario: "summer", links: [] })).toBeNull()
    expect(
      scenarioPayload({ ...base, scenario: "road", links: [local as LinkChangeInput] }),
    ).toBeNull()
    expect(
      scenarioPayload({ ...base, scenario: "winter", links: [local as LinkChangeInput] })?.links,
    ).toHaveLength(1)
    expect(
      scenarioPayload({ ...base, wayIds: [1], profile: null, scenario: "road", links: [] }),
    ).toBeNull()
    expect(scenarioPayload({ ...base, regionId: null, scenario: "road", links: [] })).toBeNull()
    expect(removalOf({ ...ferry, mode: "bus" })).toBeNull()
  })

  it("validates new links before submission", () => {
    expect(additionOf("air", "Moscow", "moscow", "2")).toBe("graph:links.sameCity")
    expect(additionOf("air", "Moscow", "", "2")).toBe("graph:links.sameCity")
    expect(additionOf("air", "Moscow", "Sochi", "0")).toBe("graph:links.hoursError")
    expect(additionOf("air", "Moscow", "Sochi", "73")).toBe("graph:links.hoursError")
    expect(additionOf("air", "Moscow", "Sochi", "72")).toMatchObject({ hours: 72 })
  })

  it("toggles links and stops at the backend limit", () => {
    const closure = airportClosure("Surgut")
    expect(toggleLink(toggleLink([], closure), closure)).toEqual([])
    const many = Array.from({ length: LINK_LIMIT }, (_, index) => airportClosure(`City ${index}`))
    expect(toggleLink(many, closure)).toHaveLength(LINK_LIMIT)
  })

  it("surfaces backend validation messages verbatim", () => {
    const message = "Intercity links connect the 180 market cities; unknown city: Moon"
    expect(rejectionMessage(new ApiError(422, "validation_error", { message }))).toBe(message)
    expect(rejectionMessage(new ApiError(500, "unexpected", { message }))).toBeNull()
    expect(rejectionMessage(new Error("offline"))).toBeNull()
  })
})
