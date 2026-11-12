import { expect, it } from "vitest"
import type { Assessment, Facility } from "@/entities/normative"
import { normativeScope } from "@/features/map-explorer/selection/normative-scope"

const regions = [
  { id: "A", name: "Pilot" },
  { id: "B", name: "Other" },
]
const result = { region: "Pilot" } as Assessment
const facilities: Facility[] = []

it("keeps an explicitly selected region and hides another region's pilot data", () => {
  const scope = normativeScope("B", "N01", result, "Pilot", regions, facilities)
  expect(scope.selection).toBe("B")
  expect(scope.regionName).toBe("Other")
  expect(scope.result).toBeNull()
  expect(scope.facilities).toBeUndefined()
})

it("shows the national overview when no region was selected", () => {
  const scope = normativeScope(null, "N01", result, "Pilot", regions, facilities)
  expect(scope.selection).toBeNull()
  expect(scope.result).toBeNull()
})

it("does not force a pilot region for the original atlas metrics", () => {
  expect(normativeScope(null, null, undefined, undefined, regions, undefined).selection).toBeNull()
})
