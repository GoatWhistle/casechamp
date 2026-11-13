import type { FeatureCollection, Geometry } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { AnalysisDetail, AnalysisOverlay } from "@/shared/api/road-analysis"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { fitPadding } from "./camera/fit-padding"
import { REGIONS_SOURCE } from "./osm-style"
import { addRoute, fadeIn, revealRoute } from "./paint/line-reveal"

const SOURCE = "road-analysis-result"
const LINE = `${SOURCE}-line`
const POINTS = `${SOURCE}-points`
const WIDTH = 4

export function useAnalysisLayer(
  engine: RefObject<LibreMap | null>,
  overlay: AnalysisOverlay | null | undefined,
  ready: boolean,
) {
  const reduced = useReducedMotion()
  const lastFocus = useRef(0)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getSource(REGIONS_SOURCE)) return
    const detail = overlay?.detail
    const data = analysisFeatures(detail)
    const style = getComputedStyle(map.getContainer())
    const color = style.getPropertyValue("--agent-action").trim()
    const way = String(detail?.result.candidate.way_id ?? "")
    const fresh = way !== "" && map.getContainer().dataset.analysisWay !== way
    if (!map.getSource(SOURCE)) {
      map.addSource(SOURCE, { type: "geojson", data, lineMetrics: true })
      addRoute(map, {
        id: LINE,
        source: SOURCE,
        color,
        width: WIDTH,
        filter: ["==", ["get", "kind"], "road"],
      })
      map.addLayer({
        id: POINTS,
        source: SOURCE,
        type: "circle",
        filter: ["==", ["get", "kind"], "settlement"],
        paint: {
          "circle-radius": ["case", ["get", "isolated"], 7, 4],
          "circle-color": [
            "case",
            ["get", "isolated"],
            style.getPropertyValue("--status-danger").trim(),
            style.getPropertyValue("--agent-action").trim(),
          ],
          "circle-stroke-width": 1,
          "circle-stroke-color": style.getPropertyValue("--surface-base").trim(),
        },
      })
    } else (map.getSource(SOURCE) as GeoJSONSource).setData(data)
    if (fresh) {
      revealRoute(map, { id: LINE, color })
      fadeIn(map, POINTS, ["circle-opacity", "circle-stroke-opacity"])
    }
    map.getContainer().dataset.analysisWay = way
    if (
      !overlay ||
      overlay.focus === 0 ||
      overlay.focus === lastFocus.current ||
      !detail?.lines.length
    )
      return
    lastFocus.current = overlay.focus
    const [xs, ys] = extent(detail.lines)
    map.stop()
    map.fitBounds(
      [
        [Math.min(...xs), Math.min(...ys)],
        [Math.max(...xs), Math.max(...ys)],
      ],
      {
        padding: fitPadding(map, 96),
        maxZoom: 12,
        duration: reduced || overlay.instant ? 0 : motionMs("--dur-map"),
      },
    )
  }, [engine, overlay, ready, reduced])
}

function extent(lines: number[][][]) {
  const coordinates = lines.flat()
  return [
    coordinates.map((p) => {
      const x = p[0] ?? 0
      return x < 0 ? x + 360 : x
    }),
    coordinates.map((p) => p[1] ?? 0),
  ] as const
}

function analysisFeatures(detail: AnalysisDetail | undefined): FeatureCollection<Geometry> {
  const data: FeatureCollection<Geometry> = { type: "FeatureCollection", features: [] }
  if (detail) {
    data.features.push({
      type: "Feature",
      properties: { kind: "road" },
      geometry: { type: "MultiLineString", coordinates: detail.lines },
    })
    for (const point of detail.settlements)
      data.features.push({
        type: "Feature",
        properties: {
          kind: "settlement",
          isolated: point.impact.newly_isolated,
          delta: point.impact.delta,
        },
        geometry: { type: "Point", coordinates: [point.longitude, point.latitude] },
      })
  }
  return data
}
