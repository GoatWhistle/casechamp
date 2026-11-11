import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import type { RoadSegment } from "@/shared/api/road-graph"
import { motionMs, prefersReducedMotion } from "@/shared/motion"
import { transparent } from "./paint/line-reveal"
import { ROAD_LAYOUT, roadOpacity, roadWidth } from "./road-paint"
import { betweenRoadParts, roadLayers, roadPart } from "./road-parts"

export function selectRoads(
  map: LibreMap,
  selected: readonly RoadSegment[],
  layers = roadLayers(map),
) {
  const ids = selected.map((road) => road.way_id)
  const width = roadWidth(ids)
  const opacity = roadOpacity(ids)
  for (const id of layers) {
    map.setPaintProperty(id, "line-width", width)
    map.setPaintProperty(id, "line-opacity", opacity)
  }
}

function removeParts(map: LibreMap, from: number) {
  const count = Number(map.getContainer().dataset.roadParts ?? 0)
  for (let index = from; index < count; index++) {
    const id = roadPart(index)
    if (map.getLayer(id)) map.removeLayer(id)
    if (map.getSource(id)) map.removeSource(id)
  }
  map.getContainer().dataset.roadParts = String(from)
}

const ROAD_MAX_ZOOM = 14
const ROAD_TOLERANCE = 0.5

export async function drawRoadParts(
  map: LibreMap,
  parts: readonly Blob[],
  signal: AbortSignal,
  selected: () => readonly RoadSegment[],
) {
  if (!parts.length) {
    removeParts(map, 0)
    return
  }
  const color = getComputedStyle(map.getContainer()).getPropertyValue("--map-road").trim()
  const fade = prefersReducedMotion() ? 0 : motionMs("--dur-panel", map.getContainer())
  for (const [index, part] of parts.entries()) {
    await betweenRoadParts(map, signal)
    if (signal.aborted) return
    const id = roadPart(index)
    const created = !map.getSource(id)
    if (created) {
      map.addSource(id, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        maxzoom: ROAD_MAX_ZOOM,
        tolerance: ROAD_TOLERANCE,
      })
      map.addLayer({
        id,
        type: "line",
        source: id,
        layout: ROAD_LAYOUT,
        paint: {
          "line-color": transparent(color),
          "line-color-transition": { duration: fade, delay: 0 },
          "line-width": roadWidth([]),
          "line-opacity": roadOpacity([]),
        },
      })
    }
    map.getContainer().dataset.roadParts = String(
      Math.max(index + 1, Number(map.getContainer().dataset.roadParts ?? 0)),
    )
    selectRoads(map, selected(), [id])
    const url = URL.createObjectURL(part)
    try {
      await (map.getSource(id) as GeoJSONSource).setData(url)
    } finally {
      URL.revokeObjectURL(url)
    }
    if (signal.aborted) return
    if (created) map.setPaintProperty(id, "line-color", color)
  }
  removeParts(map, parts.length)
}
