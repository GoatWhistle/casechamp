import { useSyncExternalStore } from "react"
import type { components } from "@/shared/api/schema.gen"

type Target = components["schemas"]["TransitMapTarget"]
let current: Target | null = null
const listeners = new Set<() => void>()
const snapshot = () => current
const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
export function showTransitJourney(target: Target | null) {
  current = target
  for (const listener of listeners) listener()
}
export function useTransitView() {
  return useSyncExternalStore(subscribe, snapshot, snapshot)
}
