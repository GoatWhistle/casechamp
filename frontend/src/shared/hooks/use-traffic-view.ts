import { useSyncExternalStore } from "react"
import {
  type TrafficJob,
  type TrafficMode,
  type TrafficRoad,
  usefulTrafficAlternatives,
} from "@/shared/api/traffic"

interface TrafficView {
  readonly job: TrafficJob | null
  readonly variant: string
  readonly mode: TrafficMode
  readonly focus: number
  readonly selected: TrafficRoad | null
  readonly automatic: boolean
}
let current: TrafficView = {
  job: null,
  variant: "baseline",
  mode: "before",
  focus: 0,
  selected: null,
  automatic: true,
}
const listeners = new Set<() => void>()
const snapshot = () => current
const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
function publish(next: TrafficView) {
  current = next
  for (const listener of listeners) listener()
}
export function useTrafficView() {
  return useSyncExternalStore(subscribe, snapshot, snapshot)
}
export function showTrafficView(job: TrafficJob, variant?: string, mode?: TrafficMode) {
  const selected = variant ?? preferredVariant(job)
  publish({
    job,
    variant: selected,
    mode: mode ?? "project",
    focus: performance.now(),
    selected: null,
    automatic: variant === undefined,
  })
}
export function updateTrafficView(job: TrafficJob) {
  if (current.job?.id !== job.id) return
  const available = usefulTrafficAlternatives(job).some((row) => row.id === current.variant)
  const choose = current.automatic || (!available && current.variant !== "baseline")
  const variant = choose ? preferredVariant(job) : current.variant
  const mode = choose ? "project" : current.mode
  const changed = current.variant !== variant || (!current.job.roads.length && job.roads.length > 0)
  const focus = current.automatic && changed ? performance.now() : current.focus
  publish({ ...current, job, variant, mode, focus })
}
export function clearTrafficView() {
  publish({ ...current, job: null, selected: null })
}
export function selectTrafficRoad(selected: TrafficRoad | null) {
  publish({ ...current, selected })
}

function preferredVariant(job: TrafficJob): string {
  if (job.version === "municipal_fixed_od_v1") return job.alternatives[0]?.id ?? "baseline"
  const region = job.indices[0]?.region
  const ranked = usefulTrafficAlternatives(job)
    .filter((row) => row.indices?.some((index) => index.region === region))
    .sort(
      (a, b) =>
        (b.indices?.find((index) => index.region === region)?.delta ?? -Infinity) -
        (a.indices?.find((index) => index.region === region)?.delta ?? -Infinity),
    )
  return ranked[0]?.id ?? "baseline"
}
