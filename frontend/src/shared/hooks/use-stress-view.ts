import { useSyncExternalStore } from "react"
import type { StressImpact, StressRegion, StressRouteComparison } from "@/shared/api/road-stress"

interface StressView {
  readonly showPoints?: boolean
  readonly selected?: StressImpact | null
  readonly selectedRegion?: string
  readonly closed?: number[][][]
  readonly regions?: readonly StressRegion[]
  readonly jobId: string | null
  readonly impacts: readonly StressImpact[]
  readonly route: StressRouteComparison | null
  readonly focus: number
}
let current: StressView = { jobId: null, impacts: [], route: null, focus: 0 }
const listeners = new Set<() => void>()
const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
const snapshot = () => current
export function showStressView(value: Omit<StressView, "focus">) {
  current = {
    ...(value.jobId === current.jobId ? current : {}),
    selected: null,
    selectedRegion: "",
    ...value,
    showPoints: value.showPoints ?? !value.route,
    focus: performance.now(),
  }
  for (const listener of listeners) listener()
}
export function useStressView() {
  return useSyncExternalStore(subscribe, snapshot, snapshot)
}

export function updateStressGeometry(jobId: string, closed: number[][][]) {
  if (current.jobId !== jobId) return
  current = { ...current, closed }
  for (const listener of listeners) listener()
}

export function selectStressImpact(selected: StressImpact) {
  current = { ...current, selected }
  for (const listener of listeners) listener()
}
export function selectStressRegion(selectedRegion: string) {
  current = { ...current, selectedRegion, selected: null }
  for (const listener of listeners) listener()
}
