import type { FeatureCollection, LineString } from "geojson"
import type { RoadRenderView, RoadView } from "@/shared/api/road-graph"

const MAJOR = new Set(["motorway", "trunk"])
const PRIMARY = new Set(["primary", "motorway_link", "trunk_link"])
const SECONDARY = new Set(["secondary", "primary_link"])

function roadRank(highway: string): number {
  if (MAJOR.has(highway)) return 0
  if (PRIMARY.has(highway)) return 1
  return SECONDARY.has(highway) ? 2 : 3
}

export function prepareRoadView(view: RoadView): RoadRenderView {
  const choices = new Map<number, RoadView["segments"][number]>()
  const geometry: Blob[] = []
  const segments = [...view.segments].sort((a, b) => roadRank(a.highway) - roadRank(b.highway))
  for (let offset = 0; offset < segments.length; offset += 2000) {
    const data: FeatureCollection<LineString> = {
      type: "FeatureCollection",
      features: segments.slice(offset, offset + 2000).map((road, index) => {
        if (choices.size < 12 && !choices.has(road.way_id)) choices.set(road.way_id, road)
        const { coordinates, ...properties } = road
        return {
          type: "Feature",
          id: offset + index,
          properties,
          geometry: { type: "LineString", coordinates },
        }
      }),
    }
    geometry.push(new Blob([JSON.stringify(data)], { type: "application/json" }))
  }
  return {
    ...view,
    segments: [...choices.values()],
    segmentCount: view.segments.length,
    geometry,
  }
}
