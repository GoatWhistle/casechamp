import type { Map as LibreMap } from "maplibre-gl"
import { motionMs } from "@/shared/motion"
import { ease } from "./line-reveal"
import { REGIONS_SOURCE } from "./osm-style"

export function regionSteps(
  features: ReadonlyMap<string, { readonly id: number | string | undefined }>,
  stepOf: (id: string) => number,
): Map<number, number> {
  const steps = new Map<number, number>()
  for (const [regionId, feature] of features)
    if (typeof feature.id === "number") steps.set(feature.id, stepOf(regionId))
  return steps
}

export function recolorRegions(
  map: LibreMap,
  steps: ReadonlyMap<number, number>,
  current: Map<number, number>,
  instant: boolean,
): () => void {
  const ids = [...steps.keys()]
  for (const id of ids) {
    const step = steps.get(id) ?? 0
    map.setFeatureState(
      { source: REGIONS_SOURCE, id },
      { previous: current.get(id) ?? step, step, mix: instant ? 1 : 0 },
    )
    current.set(id, step)
  }
  if (instant) return () => undefined
  const duration = motionMs("--dur-panel", map.getContainer())
  const start = performance.now()
  let frame = requestAnimationFrame(function tick(now) {
    const progress = Math.min(1, (now - start) / duration)
    for (const id of ids)
      map.setFeatureState({ source: REGIONS_SOURCE, id }, { mix: ease(progress) })
    if (progress < 1) frame = requestAnimationFrame(tick)
  })
  return () => cancelAnimationFrame(frame)
}
