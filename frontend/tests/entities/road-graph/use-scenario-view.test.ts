import { describe, expect, it } from "vitest"
import { scenarioViewOf } from "@/entities/road-graph/use-scenario-view"

describe("road scenario navigation", () => {
  it("does not restore the removed manual road-connection form from an old URL", () => {
    expect(scenarioViewOf(new URLSearchParams("analysis_mode=connection"))).toBe("home")
  })
  it("retains manual existing-road changes and geographic development entry points", () => {
    expect(scenarioViewOf(new URLSearchParams("analysis_mode=roads"))).toBe("roads")
    expect(scenarioViewOf(new URLSearchParams("analysis_mode=improvement"))).toBe("improvement")
  })
})
