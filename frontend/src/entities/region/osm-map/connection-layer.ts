import type { FeatureCollection, LineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import type { RoadJob } from "@/shared/api/road-graph"
import { addRoute, revealRoute } from "./paint/line-reveal"

const CONNECTION_LAYER = "scenario-connection"
const WIDTH = 4

export function drawConnection(map: LibreMap, addition: RoadJob["addition"] | undefined) {
  const coordinates = addition?.coordinates ?? null
  const data: FeatureCollection<LineString> = {
    type: "FeatureCollection",
    features: coordinates
      ? [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates } }]
      : [],
  }
  const color = getComputedStyle(map.getContainer()).getPropertyValue("--data-gain-3").trim()
  const key = coordinates ? JSON.stringify(coordinates) : ""
  const fresh = key !== "" && map.getContainer().dataset.connection !== key
  if (!map.getSource(CONNECTION_LAYER)) {
    map.addSource(CONNECTION_LAYER, { type: "geojson", data, lineMetrics: true })
    addRoute(map, { id: CONNECTION_LAYER, source: CONNECTION_LAYER, color, width: WIDTH })
  } else {
    ;(map.getSource(CONNECTION_LAYER) as GeoJSONSource).setData(data)
  }
  if (fresh) revealRoute(map, { id: CONNECTION_LAYER, color })
  map.getContainer().dataset.connection = key
}
