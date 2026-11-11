import type { FeatureCollection, MultiLineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { CorridorOverlay } from "@/shared/api/chat-calculation"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { addRoute, raiseRoute, removeRoute, revealRoute } from "./line-reveal"

const SOURCE = "road-corridor-closure"
const WIDTH = 4

export function useCorridorLayer(
  engine: RefObject<LibreMap | null>,
  overlay: CorridorOverlay | null | undefined,
  ready: boolean,
) {
  const reduced = useReducedMotion()
  const focused = useRef(0)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    if (!overlay) {
      clearCorridor(map)
      focused.current = 0
      return
    }
    const lines = overlay.calculation.corridor.lines
    const data: FeatureCollection<MultiLineString> = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          properties: {},
          geometry: { type: "MultiLineString", coordinates: lines },
        },
      ],
    }
    const color = getComputedStyle(map.getContainer()).getPropertyValue("--status-danger").trim()
    const fresh = map.getContainer().dataset.corridorId !== overlay.calculation.corridor.id
    if (!map.getSource(SOURCE)) {
      map.addSource(SOURCE, { type: "geojson", data, lineMetrics: true })
      addRoute(map, { id: SOURCE, source: SOURCE, color, width: WIDTH })
    } else (map.getSource(SOURCE) as GeoJSONSource).setData(data)
    raiseRoute(map, SOURCE)
    if (fresh) revealRoute(map, { id: SOURCE, color })
    map.getContainer().dataset.corridorId = overlay.calculation.corridor.id
    if (focused.current === overlay.focus || !lines.length) return
    focused.current = overlay.focus
    const points = lines.flat()
    const xs = points.map((point) => point[0] ?? 0)
    const ys = points.map((point) => point[1] ?? 0)
    map.stop()
    map.fitBounds(
      [
        [Math.min(...xs), Math.min(...ys)],
        [Math.max(...xs), Math.max(...ys)],
      ],
      {
        padding: 96,
        maxZoom: 12,
        duration: reduced || overlay.instant ? 0 : motionMs("--dur-map"),
      },
    )
  }, [engine, overlay, ready, reduced])
}

function clearCorridor(map: LibreMap) {
  removeRoute(map, SOURCE)
  if (map.getSource(SOURCE)) map.removeSource(SOURCE)
  delete map.getContainer().dataset.corridorId
}
