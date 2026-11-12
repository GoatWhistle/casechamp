import { ApiError, api, unwrap } from "./client"
import type { components } from "./schema.gen"

export type TrafficJob = Required<components["schemas"]["TrafficJob"]>
export type TrafficRoad = components["schemas"]["TrafficRoad"]
export type TrafficAlternative = components["schemas"]["TrafficAlternative"]
export type TrafficMode = "project" | "before" | "after" | "difference"

export const trafficTerminal = (status: string) =>
  ["completed", "failed", "cancelled"].includes(status)

export async function trafficJob(id: string, signal: AbortSignal): Promise<TrafficJob> {
  const value = await unwrap(
    api.GET("/api/v1/traffic-jobs/{job_id}", { params: { path: { job_id: id } }, signal }),
  )
  if (!isTrafficJob(value)) throw new ApiError(502, "unexpected_response")
  return value
}

export function isTrafficJob(value: unknown): value is TrafficJob {
  if (typeof value !== "object" || value === null) return false
  const row = value as Record<string, unknown>
  return (
    typeof row.id === "string" &&
    row.id.startsWith("traffic-") &&
    ["queued", "running", "completed", "failed", "cancelled"].includes(String(row.status)) &&
    typeof row.stage === "string" &&
    typeof row.provenance === "string" &&
    Array.isArray(row.bounds) &&
    row.bounds.length === 4 &&
    row.bounds.every(Number.isFinite) &&
    Array.isArray(row.roads) &&
    Array.isArray(row.zones) &&
    Array.isArray(row.alternatives) &&
    Array.isArray(row.indices) &&
    typeof row.version === "string" &&
    typeof row.completed === "number" &&
    typeof row.total === "number" &&
    typeof row.scope === "object" &&
    row.scope !== null
  )
}

export function usefulTrafficAlternatives(job: TrafficJob, region?: string) {
  const before = job.baseline?.mean_trip_minutes
  return job.alternatives.filter((row) => {
    if (row.kind === "connection" && row.housing_clearance !== true) return false
    const local =
      before !== null &&
      before !== undefined &&
      row.after.mean_trip_minutes !== null &&
      row.after.mean_trip_minutes !== undefined &&
      before - row.after.mean_trip_minutes >= 0.05
    return (
      local ||
      row.indices?.some((value) => (!region || value.region === region) && value.delta >= 0.0001)
    )
  })
}
