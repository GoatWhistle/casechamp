import type { components } from "./schema.gen"

export type StressRegion = components["schemas"]["StressRegion"]
export type StressJob = components["schemas"]["StressJob"]
export type StressImpact = components["schemas"]["StressImpact"]
export type StressSummary = components["schemas"]["StressSummary"]
export type StressRouteComparison = components["schemas"]["StressRouteComparison"]

export function isStressJob(value: unknown): value is StressJob {
  if (!record(value)) return false
  return (
    typeof value.id === "string" &&
    typeof value.version === "string" &&
    Array.isArray(value.way_ids) &&
    value.way_ids.every((id: unknown) => Number.isSafeInteger(id)) &&
    ["queued", "running", "completed", "failed", "cancelled"].includes(String(value.status)) &&
    (value.regions === undefined || (Array.isArray(value.regions) && value.regions.every(isRegion)))
  )
}
function isRegion(value: unknown) {
  return (
    record(value) &&
    typeof value.name === "string" &&
    finite(value.settlements) &&
    finite(value.population) &&
    finite(value.isolated_population)
  )
}

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null
const finite = (value: unknown) => typeof value === "number" && Number.isFinite(value)
function isPoint(value: unknown) {
  return (
    record(value) &&
    typeof value.id === "string" &&
    typeof value.name === "string" &&
    typeof value.region === "string" &&
    finite(value.population) &&
    finite(value.node) &&
    finite(value.snap_km) &&
    finite(value.longitude) &&
    finite(value.latitude)
  )
}
function isRoute(value: unknown) {
  if (!record(value)) return false
  return (
    typeof value.status === "string" &&
    (value.hours === null || finite(value.hours)) &&
    (value.km === null || finite(value.km)) &&
    Array.isArray(value.coordinates) &&
    value.coordinates.every((p: unknown) => Array.isArray(p) && p.length === 2 && p.every(finite))
  )
}
export function isStressRoute(value: unknown): value is StressRouteComparison {
  return (
    record(value) &&
    isPoint(value.origin) &&
    isPoint(value.destination) &&
    isRoute(value.before) &&
    isRoute(value.after)
  )
}
export function isStressRoutes(value: unknown): boolean {
  return value === undefined || (record(value) && Object.values(value).every(isStressRoute))
}
