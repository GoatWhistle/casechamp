import type { FeatureCollection, Geometry } from "geojson"
import type {
  FilterSpecification,
  GeoJSONSource,
  Map as LibreMap,
  LineLayerSpecification,
} from "maplibre-gl"

export const SOURCE = "agent-traffic"
export const LINES = ["road", "relief", "project", "closure", "connection"] as const
const ORDER = [
  "road",
  "relief",
  "project-outline",
  "project",
  "closure",
  "connection-outline",
  "connection",
]

export function paintTraffic(map: LibreMap, data: FeatureCollection<Geometry>) {
  if (map.getSource(SOURCE)) (map.getSource(SOURCE) as GeoJSONSource).setData(data)
  else map.addSource(SOURCE, { type: "geojson", data })
  for (const role of ["zones", "scope", "area"]) {
    if (map.getLayer(`${SOURCE}-${role}`)) map.removeLayer(`${SOURCE}-${role}`)
  }
  for (const layer of layers(map)) {
    if (map.getLayer(layer.id)) map.removeLayer(layer.id)
    map.addLayer(layer)
  }
  raiseTrafficLayers(map)
}

export function raiseTrafficLayers(map: LibreMap) {
  for (const role of ORDER)
    if (map.getLayer(`${SOURCE}-${role}`)) map.moveLayer(`${SOURCE}-${role}`)
}

function layers(map: LibreMap): LineLayerSpecification[] {
  const style = getComputedStyle(map.getContainer())
  const red = style.getPropertyValue("--agent-action").trim()
  const green = style.getPropertyValue("--agent-new-road").trim()
  const selected: FilterSpecification = [
    "all",
    ["==", ["get", "project"], true],
    ["!=", ["get", "role"], "connection"],
  ]
  return [
    {
      id: `${SOURCE}-road`,
      source: SOURCE,
      type: "line",
      filter: ["all", ["==", ["get", "role"], "road"], ["!=", ["get", "project"], true]],
      paint: {
        "line-color": ["case", [">", ["get", "ratio"], 1], red, green],
        "line-opacity": ["case", [">", ["get", "ratio"], 1], 0.9, 0.35],
        "line-width": ["interpolate", ["linear"], ["get", "flow"], 0, 1, 1800, 4, 5000, 7],
      },
    },
    {
      id: `${SOURCE}-relief`,
      source: SOURCE,
      type: "line",
      filter: ["all", ["==", ["get", "role"], "relief"], ["!=", ["get", "project"], true]],
      paint: { "line-color": red, "line-opacity": 0.45, "line-width": 3, "line-dasharray": [1, 3] },
    },
    {
      id: `${SOURCE}-project-outline`,
      source: SOURCE,
      type: "line",
      filter: selected,
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": style.getPropertyValue("--surface-base").trim(), "line-width": 10 },
    },
    {
      id: `${SOURCE}-project`,
      source: SOURCE,
      type: "line",
      filter: ["all", selected, ["!=", ["get", "closed"], true]],
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": red, "line-width": 6 },
    },
    {
      id: `${SOURCE}-closure`,
      source: SOURCE,
      type: "line",
      filter: ["==", ["get", "closed"], true],
      paint: { "line-color": red, "line-width": 6, "line-dasharray": [1, 1] },
    },
    {
      id: `${SOURCE}-connection-outline`,
      source: SOURCE,
      type: "line",
      filter: ["==", ["get", "role"], "connection"],
      layout: { "line-cap": "round" },
      paint: {
        "line-color": style.getPropertyValue("--agent-new-road-outline").trim(),
        "line-width": 9,
        "line-dasharray": [2, 2],
      },
    },
    {
      id: `${SOURCE}-connection`,
      source: SOURCE,
      type: "line",
      filter: ["==", ["get", "role"], "connection"],
      layout: { "line-cap": "round" },
      paint: { "line-color": green, "line-width": 6, "line-dasharray": [2, 2] },
    },
  ]
}
