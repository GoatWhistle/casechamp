import type { FeatureCollection, LineString, Point } from "geojson"
import type { ExpressionSpecification, GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import { fadeIn, revealLines } from "./paint/line-reveal"

const TRANSIT_SOURCE = "region-transit"
const AIR = `${TRANSIT_SOURCE}-air`
const RAIL = `${TRANSIT_SOURCE}-rail`
const ENDS = `${TRANSIT_SOURCE}-ends`
const WIDTH: ExpressionSpecification = ["interpolate", ["linear"], ["zoom"], 3, 1.2, 8, 2.4]

export function useTransitLayer(
  engine: RefObject<LibreMap | null>,
  data: FeatureCollection<LineString>,
  ready: boolean,
) {
  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    const ends = endpoints(data)
    if (!map.getSource(TRANSIT_SOURCE)) addTransitLayers(map, data, ends)
    else {
      ;(map.getSource(TRANSIT_SOURCE) as GeoJSONSource).setData(data)
      ;(map.getSource(ENDS) as GeoJSONSource | undefined)?.setData(ends)
    }
    map.getContainer().dataset.transitConnections = String(data.features.length)
    if (!data.features.length) return
    const air = getComputedStyle(map.getContainer()).getPropertyValue("--mode-air").trim()
    revealLines(map, AIR, [{ id: AIR, color: air }])
    fadeIn(map, RAIL, ["line-opacity"])
    fadeIn(map, ENDS, ["circle-opacity", "circle-stroke-opacity"], true)
  }, [engine, data, ready])
}

function endpoints(data: FeatureCollection<LineString>): FeatureCollection<Point> {
  const seen = new Set<string>()
  const features: FeatureCollection<Point>["features"] = []
  for (const line of data.features) {
    const { coordinates } = line.geometry
    for (const point of [coordinates[0], coordinates.at(-1)]) {
      if (!point) continue
      const key = `${line.properties?.mode}:${point.join(",")}`
      if (seen.has(key)) continue
      seen.add(key)
      features.push({
        type: "Feature",
        properties: { mode: line.properties?.mode },
        geometry: { type: "Point", coordinates: point },
      })
    }
  }
  return { type: "FeatureCollection", features }
}

function addTransitLayers(
  map: LibreMap,
  data: FeatureCollection<LineString>,
  ends: FeatureCollection<Point>,
) {
  const colors = getComputedStyle(map.getContainer())
  const air = colors.getPropertyValue("--mode-air").trim()
  const rail = colors.getPropertyValue("--mode-rail").trim()
  map.addSource(TRANSIT_SOURCE, { type: "geojson", data, lineMetrics: true })
  map.addLayer({
    id: RAIL,
    type: "line",
    source: TRANSIT_SOURCE,
    filter: ["==", ["get", "mode"], "rail"],
    layout: { "line-cap": "round" },
    paint: {
      "line-color": rail,
      "line-width": WIDTH,
      "line-dasharray": [1, 2.5],
    },
  })
  map.addLayer({
    id: AIR,
    type: "line",
    source: TRANSIT_SOURCE,
    filter: ["==", ["get", "mode"], "air"],
    layout: { "line-cap": "round", "line-join": "round" },
    paint: {
      "line-width": WIDTH,
      "line-opacity": 0.85,
      "line-gradient": [
        "interpolate",
        ["linear"],
        ["line-progress"],
        0,
        "rgba(0, 0, 0, 0)",
        1,
        "rgba(0, 0, 0, 0)",
      ],
    },
  })
  map.addSource(ENDS, { type: "geojson", data: ends })
  map.addLayer({
    id: ENDS,
    type: "circle",
    source: ENDS,
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 2.5, 8, 4],
      "circle-color": ["match", ["get", "mode"], "air", air, rail],
      "circle-stroke-color": colors.getPropertyValue("--surface-base").trim(),
      "circle-stroke-width": 1.5,
    },
  })
}
