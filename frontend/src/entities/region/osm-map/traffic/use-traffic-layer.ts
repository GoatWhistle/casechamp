import type { Map as LibreMap, MapLayerMouseEvent } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import { selectTrafficRoad, useTrafficView } from "@/shared/hooks/use-traffic-view"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { fitPadding } from "../camera/fit-padding"
import { REGIONS_SOURCE } from "../osm-style"
import { trafficBounds, trafficFeatures } from "./traffic-features"
import { LINES, paintTraffic, SOURCE } from "./traffic-paint"

export function useTrafficLayer(engine: RefObject<LibreMap | null>, ready: boolean) {
  const view = useTrafficView()
  const reduced = useReducedMotion()
  const focus = useRef(0)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getSource(REGIONS_SOURCE)) return
    const data = trafficFeatures(view.job, view.variant, view.mode)
    paintTraffic(map, data)
    if (!view.job || view.focus === focus.current) return
    focus.current = view.focus
    const [w, s, e, n] = trafficBounds(view.job, view.variant)
    if (w === undefined || s === undefined || e === undefined || n === undefined) return
    map.stop()
    map.fitBounds(
      [
        [w, s],
        [e, n],
      ],
      {
        padding: fitPadding(map, 72),
        maxZoom: view.variant === "baseline" ? 13 : 16,
        duration: reduced ? 0 : motionMs("--dur-map"),
      },
    )
  }, [engine, ready, view.job, view.variant, view.mode, view.focus, reduced])

  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    const inspect = (event: MapLayerMouseEvent) => {
      const layers = LINES.map((role) => `${SOURCE}-${role}`).filter((id) => map.getLayer(id))
      if (!layers.length) return
      const feature = map.queryRenderedFeatures(event.point, { layers })[0]
      if (!feature || !view.job) return
      const roads =
        view.job.alternatives.find((row) => row.id === view.variant)?.roads ?? view.job.roads
      selectTrafficRoad(roads[Number(feature.properties.index)] ?? null)
    }
    map.on("click", inspect)
    return () => {
      map.off("click", inspect)
    }
  }, [engine, ready, view.job, view.variant])
}
