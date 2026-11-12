import { describe, expect, it } from "vitest"
import { trafficBounds, trafficFeatures } from "@/entities/region/osm-map/traffic/traffic-features"
import type { TrafficJob, TrafficRoad } from "@/shared/api/traffic"

const road: TrafficRoad = {
  way_id: 1,
  coordinates: [
    [42, 44],
    [42.1, 44.1],
  ],
  flow_before: 100,
  flow_after: 60,
  ratio_before: 0.8,
  ratio_after: 0.4,
  project: true,
  new_link: false,
}
const metrics = {
  vehicle_hours: 1,
  unserved_vehicles: 0,
  overloaded_edges: 0,
  relative_gap: 0,
  converged: true,
}
const job: TrafficJob = {
  id: "traffic-test",
  version: "v2",
  status: "completed",
  stage: "completed",
  completed: 1,
  total: 1,
  scope: {
    objective: "connectivity",
    places: [],
    region: "",
    bounds: [],
    demand_multiplier: 1,
    pair_flow: 1000,
    max_projects: 3,
  },
  bounds: [41, 43, 43, 45],
  zones: [{ longitude: 42, latitude: 44, population: 200 }],
  baseline: metrics,
  roads: [road],
  alternatives: [
    {
      id: "new",
      housing_clearance: true,
      kind: "connection",
      way_ids: [],
      length_km: 1,
      overload_increase: 0,
      objective_unit: "",
      vehicle_hours_saved: 1,
      after: metrics,
      roads: [road, { ...road, way_id: -1, flow_before: 0, flow_after: 40, new_link: true }],
      indices: [],
      road_names: [],
    },
  ],
  indices: [],
  provenance: "{}",
  error: "",
}

describe("traffic map", () => {
  it("shows only the proposal by default, not unrelated loaded streets", () => {
    const unrelated = { ...road, project: false, way_id: 2 }
    const data = {
      ...job,
      alternatives: [
        {
          ...(job.alternatives[0] as NonNullable<(typeof job.alternatives)[0]>),
          roads: [road, unrelated],
        },
      ],
    }
    expect(trafficFeatures(data, "new", "project").features).toHaveLength(1)
    expect(trafficFeatures({ ...job, status: "running" }, "new", "after").features).toHaveLength(0)
  })
  it("rejects old new-link proposals without housing clearance", () => {
    const data = {
      ...job,
      alternatives: [
        {
          ...(job.alternatives[0] as NonNullable<(typeof job.alternatives)[0]>),
          housing_clearance: null,
        },
      ],
    }
    expect(trafficFeatures(data, "new", "project").features).toHaveLength(0)
  })
  it("focuses a selected road proposal instead of the whole calculation window", () => {
    expect(trafficBounds(job, "new")).toEqual([42, 44, 42.1, 44.1])
    expect(trafficBounds(job, "baseline")).toEqual(job.bounds)
  })
  it("highlights only roads even when the saved job has houses, zones and bounds", () => {
    const result = trafficFeatures(job, "new", "after")
    expect(result.features).toHaveLength(2)
    expect(result.features.every((feature) => feature.geometry.type === "LineString")).toBe(true)
  })
  it("does not draw a proposed road as existing before construction", () => {
    const before = trafficFeatures(job, "new", "before")
    const after = trafficFeatures(job, "new", "after")
    expect(before.features.some((feature) => feature.properties?.role === "connection")).toBe(false)
    expect(after.features.some((feature) => feature.properties?.role === "connection")).toBe(true)
  })
  it("distinguishes reduced load from new construction", () => {
    const result = trafficFeatures(job, "new", "difference")
    expect(result.features.map((feature) => feature.properties?.role)).toEqual([
      "relief",
      "connection",
    ])
    expect(result.features.map((feature) => feature.properties?.flow)).toEqual([40, 40])
  })
})
