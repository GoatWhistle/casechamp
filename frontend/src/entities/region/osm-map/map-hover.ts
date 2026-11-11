import type { Map as LibreMap, MapLayerMouseEvent, PointLike } from "maplibre-gl"
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

function overAirport(map: LibreMap, point: PointLike): boolean {
  return (
    map.getLayer(AIRPORT_LAYER) !== undefined &&
    map.queryRenderedFeatures(point, { layers: [AIRPORT_LAYER] }).length > 0
  )
}

export function bindHover(
  map: LibreMap,
  setHover: (id: number | null) => void,
  report: HoverReport,
  regionOf: RegionOf,
) {
  if (!globalThis.matchMedia?.(FINE_POINTER).matches) return
  let pointer: Pointer | null = null
  const show = (id: number | null, current: Pointer) => {
    setHover(id)
    report(overAirport(map, current.point) ? null : regionOf(id), current.x, current.y)
  }
  const pick = (current: Pointer) => {
    const feature = map.queryRenderedFeatures(current.point, { layers: [FILL_LAYER] })[0]
    show(typeof feature?.id === "number" ? feature.id : null, current)
  }
  map.on("mousemove", FILL_LAYER, (event: MapLayerMouseEvent) => {
    pointer = {
      point: event.point,
      x: event.originalEvent.clientX,
      y: event.originalEvent.clientY,
    }
    if (map.isMoving()) return
    const id = event.features?.[0]?.id
    show(typeof id === "number" ? id : null, pointer)
  })
  map.on("mouseleave", FILL_LAYER, () => {
    pointer = null
    setHover(null)
    report(null, 0, 0)
  })
  map.on("dragstart", () => report(null, 0, 0))
  map.on("moveend", () => {
    if (pointer) pick(pointer)
  })
}
