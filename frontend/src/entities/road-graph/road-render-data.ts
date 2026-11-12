import type { FeatureCollection, LineString } from "geojson"
import type { RoadFocus, RoadRenderView, RoadView } from "@/shared/api/road-graph"

import { prepareRegionIntersection } from "./road-region-geometry"

const FIRST_BATCH = 2000
const MAX_SOURCES = 6

const MAJOR = new Set(["motorway", "trunk"])
const PRIMARY = new Set(["primary", "motorway_link", "trunk_link"])
const SECONDARY = new Set(["secondary", "primary_link"])

function roadRank(highway: string): number {
  if (MAJOR.has(highway)) return 0
  if (PRIMARY.has(highway)) return 1
  return SECONDARY.has(highway) ? 2 : 3
}

export function prepareRoadView(view: RoadView, focus?: RoadFocus | null): RoadRenderView {
  const intersects = focus ? prepareRegionIntersection(focus) : null
  const connected = new Set(
    view.segments.filter((road) => intersects?.(road.coordinates)).map((road) => road.way_id),
  )
  const choices = new Map<number, RoadView["segments"][number]>()
  const geometry: Blob[] = []
  const segments = [...view.segments].sort((a, b) => roadRank(a.highway) - roadRank(b.highway))
  const tailSize = Math.max(
    FIRST_BATCH,
    Math.ceil((segments.length - FIRST_BATCH) / (MAX_SOURCES - 1)),
  )
  for (let offset = 0; offset < segments.length; ) {
    const size = offset === 0 ? FIRST_BATCH : tailSize
    const data: FeatureCollection<LineString> = {
      type: "FeatureCollection",
      features: segments.slice(offset, offset + size).map((road, index) => {
        if (choices.size < 12 && !choices.has(road.way_id)) choices.set(road.way_id, road)
        const { coordinates, ...properties } = road
        return {
          type: "Feature",
          id: offset + index,
          properties: { ...properties, focus_connected: !focus || connected.has(road.way_id) },
          geometry: { type: "LineString", coordinates },
        }
      }),
    }
    geometry.push(new Blob([JSON.stringify(data)], { type: "application/json" }))
    offset += size
  }
  return {
    ...view,
    focusRegionId: focus?.id ?? null,
    segments: [...choices.values()],
    segmentCount: view.segments.length,
    geometry,
  }
}
