import type {
  ExpressionSpecification,
  FilterSpecification,
  Map as LibreMap,
  LineLayerSpecification,
} from "maplibre-gl"
import { motionMs, prefersReducedMotion } from "@/shared/motion"

const EDGE = 0.06
const START = 0.0001
const HALO_EXTRA = 4
const DRAW_ARRIVAL = 0.7

const frames = new Map<string, number>()

export function ease(value: number): number {
  return 1 - (1 - value) ** 3
}

export function transparent(color: string): string {
  const hex = /^#([0-9a-f]{6})$/i.exec(color.trim())?.[1]
  if (!hex) return "rgba(0, 0, 0, 0)"
  const channel = (offset: number) => Number.parseInt(hex.slice(offset, offset + 2), 16)
  return `rgba(${channel(0)}, ${channel(2)}, ${channel(4)}, 0)`
}

function revealGradient(color: string, progress: number): ExpressionSpecification {
  if (progress >= 1) return ["interpolate", ["linear"], ["line-progress"], 0, color, 1, color]
  const clear = transparent(color)
  const head = Math.max(progress, START)
  const tail = Math.min(1, head + EDGE)
  const stops: (number | string)[] = [0, color, head, color, tail, clear]
  if (tail < 1) stops.push(1, clear)
  return ["interpolate", ["linear"], ["line-progress"], ...stops] as ExpressionSpecification
}

export interface RevealTarget {
  readonly id: string
  readonly color: string
}

export function revealLines(map: LibreMap, key: string, targets: readonly RevealTarget[]) {
  cancelAnimationFrame(frames.get(key) ?? 0)
  const paint = (progress: number) => {
    for (const target of targets)
      if (map.getLayer(target.id))
        map.setPaintProperty(target.id, "line-gradient", revealGradient(target.color, progress))
  }
  const duration = prefersReducedMotion() ? 0 : motionMs("--dur-draw", map.getContainer())
  if (duration <= 1) {
    paint(1)
    return
  }
  const start = performance.now()
  paint(0)
  const tick = (now: number) => {
    const progress = Math.min(1, (now - start) / duration)
    paint(ease(progress))
    if (progress < 1) frames.set(key, requestAnimationFrame(tick))
    else frames.delete(key)
  }
  frames.set(key, requestAnimationFrame(tick))
}

export interface RouteSpec {
  readonly id: string
  readonly source: string
  readonly color: string
  readonly width: number
  readonly filter?: FilterSpecification
}

export function routeIds(id: string): readonly [casing: string, line: string] {
  return [`${id}-casing`, id]
}

export function addRoute(map: LibreMap, spec: RouteSpec) {
  const [casing, line] = routeIds(spec.id)
  const halo = getComputedStyle(map.getContainer()).getPropertyValue("--surface-base").trim()
  const base = {
    type: "line",
    source: spec.source,
    layout: { "line-cap": "round", "line-join": "round" },
    ...(spec.filter === undefined ? {} : { filter: spec.filter }),
  } as const
  map.addLayer({
    ...base,
    id: casing,
    paint: { "line-width": spec.width + HALO_EXTRA, "line-gradient": revealGradient(halo, 1) },
  } satisfies LineLayerSpecification)
  map.addLayer({
    ...base,
    id: line,
    paint: { "line-width": spec.width, "line-gradient": revealGradient(spec.color, 1) },
  } satisfies LineLayerSpecification)
}

export function revealRoute(map: LibreMap, spec: Pick<RouteSpec, "id" | "color">) {
  const [casing, line] = routeIds(spec.id)
  const halo = getComputedStyle(map.getContainer()).getPropertyValue("--surface-base").trim()
  revealLines(map, spec.id, [
    { id: casing, color: halo },
    { id: line, color: spec.color },
  ])
}

export function removeRoute(map: LibreMap, id: string) {
  cancelAnimationFrame(frames.get(id) ?? 0)
  for (const layer of routeIds(id)) if (map.getLayer(layer)) map.removeLayer(layer)
}

export function raiseRoute(map: LibreMap, id: string) {
  for (const layer of routeIds(id)) if (map.getLayer(layer)) map.moveLayer(layer)
}

type PaintName = Parameters<LibreMap["setPaintProperty"]>[1]
type FadeProperty = "line-opacity" | "circle-opacity" | "circle-stroke-opacity"

function setFade(
  map: LibreMap,
  id: string,
  property: FadeProperty,
  value: number,
  timing: { readonly duration: number; readonly delay: number },
) {
  map.setPaintProperty(id, `${property}-transition` as PaintName, timing)
  map.setPaintProperty(id, property, value)
}

export function fadeIn(
  map: LibreMap,
  id: string,
  properties: readonly FadeProperty[],
  afterDraw = false,
) {
  if (!map.getLayer(id)) return
  const reduced = prefersReducedMotion()
  const element = map.getContainer()
  const duration = reduced ? 0 : motionMs("--dur-panel", element)
  const delay = reduced || !afterDraw ? 0 : motionMs("--dur-draw", element) * DRAW_ARRIVAL
  for (const property of properties) setFade(map, id, property, 0, { duration: 0, delay: 0 })
  requestAnimationFrame(() => {
    if (!map.getLayer(id)) return
    for (const property of properties) setFade(map, id, property, 1, { duration, delay })
  })
}
