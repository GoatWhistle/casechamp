import type { Map as LibreMap, MapGeoJSONFeature, MapMouseEvent, PointLike } from "maplibre-gl"
import { FILL_LAYER } from "./osm-style"
import { AIRPORT_LAYER } from "./use-airport-layer"

const FINE_POINTER = "(hover: hover) and (pointer: fine)"

type HoverReport = (region: string | null, x: number, y: number) => void
type RegionOf = (id: number | null) => string | null

interface Pointer {
  readonly point: PointLike
  readonly x: number
  readonly y: number
}

export function bindHover(
  map: LibreMap,
  setHover: (id: number | null) => void,
  report: HoverReport,
  regionOf: RegionOf,
  airportHover?: (feature: MapGeoJSONFeature | undefined) => void,
  highlightDelay = 0,
): () => void {
  if (!globalThis.matchMedia?.(FINE_POINTER).matches) return () => undefined
  let pointer: Pointer | null = null
  let frame: number | null = null
  let highlight: ReturnType<typeof setTimeout> | undefined
  const hide = () => {
    clearTimeout(highlight)
    if (frame !== null) cancelAnimationFrame(frame)
    frame = null
    setHover(null)
    report(null, 0, 0)
    airportHover?.(undefined)
  }
  const pick = () => {
    frame = null
    if (!pointer || map.isMoving()) return
    const layers = [FILL_LAYER, AIRPORT_LAYER].filter((id) => map.getLayer(id))
    if (!layers.length) return
    const features = map.queryRenderedFeatures(pointer.point, { layers })
    const region = features.find((feature) => feature.layer.id === FILL_LAYER)
    const airport = features.find((feature) => feature.layer.id === AIRPORT_LAYER)
    const id = typeof region?.id === "number" ? region.id : null
    if (highlightDelay > 0) highlight = setTimeout(() => setHover(id), highlightDelay)
    else setHover(id)
    report(airport ? null : regionOf(id), pointer.x, pointer.y)
    airportHover?.(airport)
  }
  const schedule = () => {
    if (pointer && frame === null && !map.isMoving()) frame = requestAnimationFrame(pick)
  }
  const move = (event: MapMouseEvent) => {
    clearTimeout(highlight)
    pointer = {
      point: event.point,
      x: event.originalEvent.clientX,
      y: event.originalEvent.clientY,
    }
    schedule()
  }
  const leave = () => {
    pointer = null
    hide()
  }
  const canvas = map.getCanvas()
  map.on("mousemove", move)
  map.on("movestart", hide)
  map.on("moveend", schedule)
  canvas.addEventListener("mouseleave", leave)
  return () => {
    hide()
    map.off("mousemove", move)
    map.off("movestart", hide)
    map.off("moveend", schedule)
    canvas.removeEventListener("mouseleave", leave)
  }
}
