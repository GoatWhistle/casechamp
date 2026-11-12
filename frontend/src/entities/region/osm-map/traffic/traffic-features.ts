import type { Feature, FeatureCollection, Geometry } from "geojson"
import type { TrafficJob, TrafficMode, TrafficRoad } from "@/shared/api/traffic"

export function trafficFeatures(
  job: TrafficJob | null,
  variant: string,
  mode: TrafficMode,
): FeatureCollection<Geometry> {
  const features: FeatureCollection<Geometry>["features"] = []
  if (job?.status !== "completed") return { type: "FeatureCollection", features }
  const selected = job.alternatives.find((row) => row.id === variant)
  if (selected?.kind === "connection" && selected.housing_clearance !== true)
    return { type: "FeatureCollection", features }
  const roads = selected?.roads ?? job.roads
  for (const [index, road] of roads.entries()) {
    const feature = roadFeature(road, index, mode)
    if (feature) features.push(feature)
  }
  return { type: "FeatureCollection", features }
}

function roadFeature(
  road: TrafficRoad,
  index: number,
  mode: TrafficMode,
): Feature<Geometry> | null {
  if (mode === "project" && !road.project) return null
  const flow =
    mode === "before"
      ? road.flow_before
      : mode === "after"
        ? road.flow_after
        : Math.abs(road.flow_after - road.flow_before)
  if ((flow <= 0 && !road.project) || (road.new_link && mode === "before")) return null
  return {
    type: "Feature",
    properties: {
      role: road.new_link
        ? "connection"
        : mode === "difference" && road.flow_after < road.flow_before
          ? "relief"
          : "road",
      index,
      flow,
      project: road.project,
    },
    geometry: { type: "LineString", coordinates: road.coordinates },
  }
}

export function trafficBounds(job: TrafficJob, variant: string): number[] {
  const selected = job.alternatives.find((row) => row.id === variant)
  const points =
    selected?.roads.filter((road) => road.project).flatMap((road) => road.coordinates) ?? []
  if (!points.length) return job.bounds
  const xs = points.map((point) => point[0] ?? 0)
  const ys = points.map((point) => point[1] ?? 0)
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]
}
