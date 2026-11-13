import { ApiError, api, unwrap } from "./client"
import type { components } from "./schema.gen"

type JobSchema = components["schemas"]["TrafficJob"]
export type TrafficJob = Required<Omit<JobSchema, "assignment_progress">> &
  Pick<JobSchema, "assignment_progress">
export type TrafficRoad = components["schemas"]["TrafficRoad"]
export type TrafficAlternative = components["schemas"]["TrafficAlternative"]
export type TrafficMode = "project" | "before" | "after" | "difference"

export const trafficTerminal = (status: string) =>
  ["completed", "failed", "cancelled"].includes(status)

export async function trafficJob(id: string, signal: AbortSignal): Promise<TrafficJob> {
  const value = await unwrap(
    id.startsWith("municipal-")
      ? api.GET("/api/v1/municipal-scenarios/{identifier}", {
          params: { path: { identifier: id } },
          signal,
        })
      : api.GET("/api/v1/traffic-jobs/{job_id}", { params: { path: { job_id: id } }, signal }),
  )
  if (!isTrafficJob(value)) throw new ApiError(502, "unexpected_response")
  return value
}

export function isTrafficJob(value: unknown): value is TrafficJob {
  if (typeof value !== "object" || value === null) return false
  const row = value as Record<string, unknown>
  return (
    validAssignmentProgress(row.assignment_progress) &&
    typeof row.id === "string" &&
    (row.id.startsWith("traffic-") || row.id.startsWith("municipal-")) &&
    ["queued", "running", "completed", "failed", "cancelled"].includes(String(row.status)) &&
    typeof row.stage === "string" &&
    typeof row.provenance === "string" &&
    Array.isArray(row.bounds) &&
    (row.bounds.length === 4 || (row.id.startsWith("municipal-") && row.bounds.length === 0)) &&
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
    if (!job.baseline?.converged || !row.after.converged) return false
    if (job.version === "municipal_fixed_od_v1") return true
    const addsLink =
      row.kind === "connection" ||
      row.roads?.some((road) => road.new_link) ||
      row.structures?.some((item) => item.kind === "connection")
    if (addsLink && row.housing_clearance !== true) return false
    const local =
      before !== null &&
      before !== undefined &&
      row.after.mean_trip_minutes !== null &&
      row.after.mean_trip_minutes !== undefined &&
      before - row.after.mean_trip_minutes >= 0.05
    const objective = Number.isFinite(row.objective_gain) && (row.objective_gain ?? 0) > 0
    return (
      objective ||
      local ||
      row.indices?.some((value) => (!region || value.region === region) && value.delta >= 0.0001)
    )
  })
}

function validAssignmentProgress(value: unknown): boolean {
  if (value === undefined || value === null) return true
  if (typeof value !== "object") return false
  const row = value as Record<string, unknown>
  return (
    typeof row.iteration === "number" &&
    Number.isInteger(row.iteration) &&
    row.iteration > 0 &&
    typeof row.relative_gap === "number" &&
    Number.isFinite(row.relative_gap) &&
    row.relative_gap >= 0 &&
    (row.tolerance === undefined ||
      (typeof row.tolerance === "number" && Number.isFinite(row.tolerance) && row.tolerance > 0))
  )
}
