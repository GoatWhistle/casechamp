import { useSyncExternalStore } from "react"
import type { components } from "@/shared/api/schema.gen"
import { showTransitJourney } from "./use-transit-view"

type Target = components["schemas"]["MunicipalAccessMapTarget"]
interface AccessView {
  readonly target: Target | null
  readonly pointId: string | null
}
let current: AccessView = { target: null, pointId: null }
const listeners = new Set<() => void>()
const snapshot = () => current
const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
function publish(next: AccessView) {
  current = next
  for (const listener of listeners) listener()
}
export function useMunicipalAccessView() {
  return useSyncExternalStore(subscribe, snapshot, snapshot)
}
export function showMunicipalAccess(target: Target) {
  showTransitJourney(null)
  publish({ target, pointId: null })
}
export function clearMunicipalAccess() {
  publish({ target: null, pointId: null })
}
export function selectMunicipalAccessPoint(pointId: string) {
  showTransitJourney(null)
  publish({ ...current, pointId })
}
