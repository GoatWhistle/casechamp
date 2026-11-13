import { type RefObject, useCallback, useEffect, useMemo, useState } from "react"
import { usePanelWidth } from "@/shared/hooks"
import { fallbackDelay } from "@/shared/motion"

export type DockPhase = "open" | "closing" | "closed" | "opening"

const WIDTH_KEY = "plexus.map-panel-width"
const COLLAPSED_KEY = "plexus.map-panel-collapsed"
const COLLAPSE_SHARE = 0.6

const SETTLED: Readonly<Record<DockPhase, DockPhase>> = {
  open: "open",
  closing: "closed",
  closed: "closed",
  opening: "open",
}

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === "1"
  } catch {
    return false
  }
}

function saveCollapsed(collapsed: boolean) {
  try {
    if (collapsed) localStorage.setItem(COLLAPSED_KEY, "1")
    else localStorage.removeItem(COLLAPSED_KEY)
  } catch {
    return
  }
}

export function usePanelDock(host: RefObject<HTMLElement | null>) {
  const width = usePanelWidth(host, WIDTH_KEY)
  const { width: current, min, commit } = width
  const [phase, setPhase] = useState<DockPhase>(() => (readCollapsed() ? "closed" : "open"))
  const collapseBelow = min * COLLAPSE_SHARE

  const collapse = useCallback((instant = false) => {
    saveCollapsed(true)
    setPhase(instant ? "closed" : "closing")
  }, [])

  const expand = useCallback(() => {
    saveCollapsed(false)
    commit(current)
    setPhase((phase) => (phase === "open" ? phase : "opening"))
  }, [commit, current])

  const settle = useCallback(() => setPhase((phase) => SETTLED[phase]), [])

  useEffect(() => {
    if (phase !== "closing" && phase !== "opening") return
    const exit = phase === "closing"
    const timer = window.setTimeout(
      settle,
      fallbackDelay(
        exit ? "--dur-exit" : "--dur-panel",
        exit ? "--reduced-fade-exit" : "--reduced-fade",
      ),
    )
    return () => window.clearTimeout(timer)
  }, [phase, settle])

  const docked = phase === "closed" || phase === "closing"
  const toggle = useMemo(() => ({ docked, collapse, expand }), [docked, collapse, expand])

  return { width, phase, collapseBelow, collapse, expand, settle, toggle }
}

export type PanelDockState = ReturnType<typeof usePanelDock>
export type DockToggleState = PanelDockState["toggle"]
