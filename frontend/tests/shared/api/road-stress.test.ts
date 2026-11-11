import { describe, expect, it } from "vitest"
import { isStressJob, isStressRoutes } from "@/shared/api/road-stress"

describe("persisted stress artifacts", () => {
  it("rejects malformed regional data before rendering", () => {
    expect(
      isStressJob({ id: "a", version: "v", way_ids: [1], status: "completed", regions: [null] }),
    ).toBe(false)
    expect(
      isStressJob({ id: "a", version: "v", way_ids: [1], status: "completed", regions: [] }),
    ).toBe(true)
  })
  it("rejects malformed saved route coordinates", () => {
    expect(isStressRoutes({ job: { before: { coordinates: [["bad", 1]] } } })).toBe(false)
    expect(isStressRoutes(undefined)).toBe(true)
  })
})
