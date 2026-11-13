import type { FeatureCollection, LineString, Point } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { NormativeRouteOverlay } from "@/shared/api/normative-map"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { fitPadding } from "../camera/fit-padding"

const SOURCE = "normative-route"
export const ROUTE_LAYERS = [
  "normative-route-outline",
  "normative-route-network",
  "normative-route-approaches",
  "normative-route-endpoints",
] as const

export function useNormativeRouteLayer(
  engine: RefObject<LibreMap | null>,
  overlay: NormativeRouteOverlay | undefined,
  ready: boolean,
  before: string,
) {
  const reduced = useReducedMotion()
  const focused = useRef("")
  useEffect(() => {
    const map = engine.current
    if (!map || !ready) return
    if (!overlay) {
      clearRoute(map)
      focused.current = ""
      return
    }
    const geometry = overlay.route.geometry
    const data = collection(geometry)
    drawRoute(map, data, before)
    map.getContainer().dataset.normativeRoutePoints = String(geometry.network_coordinates.length)
    map.getContainer().dataset.normativeRouteOrigin = overlay.route.origin_id
    map.getContainer().dataset.normativeRouteStage = overlay.route.stage
    const key = `${overlay.route.run_id}:${overlay.route.origin_id}:${overlay.route.stage}:${overlay.focus}`
    if (key === focused.current) return
    focused.current = key
    const points = [...geometry.network_coordinates, ...geometry.approaches.flat()]
    if (!points.length) return
    map.stop()
    map.fitBounds(boundsOf(points), {
      padding: fitPadding(map, 96),
      maxZoom: 14,
      duration: reduced || overlay.instant ? 0 : motionMs("--dur-panel", map.getContainer()),
    })
  }, [engine, overlay, ready, before, reduced])
}

function drawRoute(map: LibreMap, data: FeatureCollection<LineString | Point>, before: string) {
  const source = map.getSource(SOURCE) as GeoJSONSource | undefined
  if (source) {
    source.setData(data)
    return
  }
  const style = getComputedStyle(map.getContainer())
  const color = (key: string) => style.getPropertyValue(key).trim()
  const position = map.getLayer(before) ? before : undefined
  map.addSource(SOURCE, { type: "geojson", data })
  map.addLayer(
    {
      id: ROUTE_LAYERS[0],
      type: "line",
      source: SOURCE,
      filter: ["==", ["get", "kind"], "network"],
      paint: { "line-color": color("--surface-raised"), "line-width": 7 },
      layout: { "line-cap": "round", "line-join": "round" },
    },
    position,
  )
  map.addLayer(
    {
      id: ROUTE_LAYERS[1],
      type: "line",
      source: SOURCE,
      filter: ["==", ["get", "kind"], "network"],
      paint: { "line-color": color("--action-primary"), "line-width": 4 },
      layout: { "line-cap": "round", "line-join": "round" },
    },
    position,
  )
  map.addLayer(
    {
      id: ROUTE_LAYERS[2],
      type: "line",
      source: SOURCE,
      filter: ["==", ["get", "kind"], "approach"],
      paint: { "line-color": color("--text-secondary"), "line-width": 3, "line-dasharray": [2, 2] },
    },
    position,
  )
  map.addLayer({
    id: ROUTE_LAYERS[3],
    type: "circle",
    source: SOURCE,
    filter: ["==", ["get", "kind"], "endpoint"],
    paint: {
      "circle-radius": 8,
      "circle-color": color("--action-primary"),
      "circle-stroke-width": 3,
      "circle-stroke-color": color("--surface-raised"),
    },
  })
}

function clearRoute(map: LibreMap) {
  for (const id of [...ROUTE_LAYERS].reverse()) if (map.getLayer(id)) map.removeLayer(id)
  if (map.getSource(SOURCE)) map.removeSource(SOURCE)
  delete map.getContainer().dataset.normativeRoutePoints
  delete map.getContainer().dataset.normativeRouteOrigin
  delete map.getContainer().dataset.normativeRouteStage
}

function boundsOf(
  points: readonly (readonly [number, number])[],
): [[number, number], [number, number]] {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity
  for (const [x, y] of points) {
    minX = Math.min(minX, x)
    minY = Math.min(minY, y)
    maxX = Math.max(maxX, x)
    maxY = Math.max(maxY, y)
  }
  return [
    [minX, minY],
    [maxX, maxY],
  ]
}

function collection(
  geometry: NormativeRouteOverlay["route"]["geometry"],
): FeatureCollection<LineString | Point> {
  const features: FeatureCollection<LineString | Point>["features"] = []
  if (geometry.network_coordinates.length >= 2)
    features.push({
      type: "Feature",
      properties: { kind: "network" },
      geometry: { type: "LineString", coordinates: geometry.network_coordinates },
    })
  for (const line of geometry.approaches) {
    if (line.length >= 2)
      features.push({
        type: "Feature",
        properties: { kind: "approach" },
        geometry: { type: "LineString", coordinates: line },
      })
  }
  const start = geometry.approaches[0]?.[0] ?? geometry.network_coordinates[0]
  const end = geometry.approaches[1]?.at(-1) ?? geometry.network_coordinates.at(-1)
  for (const coordinates of [start, end]) {
    if (coordinates)
      features.push({
        type: "Feature",
        properties: { kind: "endpoint" },
        geometry: { type: "Point", coordinates },
      })
  }
  const data: FeatureCollection<LineString | Point> = { type: "FeatureCollection", features }
  return data
}
