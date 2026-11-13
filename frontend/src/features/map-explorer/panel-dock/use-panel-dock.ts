import { type RefObject, useCallback, useEffect, useMemo, useState } from "react"
import { flushSync } from "react-dom"
import { COMPACT_LAYOUT, useMediaQuery, usePanelWidth } from "@/shared/hooks"
import { fallbackDelay, withViewTransition } from "@/shared/motion"

export type DockPhase = "open" | "closing" | "closed" | "opening"
export type SheetSize = "half" | "full"

const WIDTH_KEY = "plexus.map-panel-width"
const COLLAPSED_KEY = "plexus.map-panel-collapsed"
const COLLAPSE_SHARE = 0.6

const FLIPPED: Readonly<Record<SheetSize, SheetSize>> = { half: "full", full: "half" }

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

function keepInView(anchor: Element | null) {
  requestAnimationFrame(() => {
    if (anchor instanceof HTMLElement) anchor.scrollIntoView?.({ block: "nearest" })
  })
}

export function usePanelDock(host: RefObject<HTMLElement | null>) {
  const width = usePanelWidth(host, WIDTH_KEY)
  const { width: current, min, commit } = width
  const compact = useMediaQuery(COMPACT_LAYOUT)
  const [phase, setPhase] = useState<DockPhase>(() => (readCollapsed() ? "closed" : "open"))
  const [sheet, setSheet] = useState<SheetSize>("half")
  const [morphing, setMorphing] = useState(false)
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

  const resize = useCallback(async (next: (size: SheetSize) => SheetSize, instant: boolean) => {
    if (instant) {
      setSheet(next)
      return
    }
    flushSync(() => setMorphing(true))
    await withViewTransition("layout", () => setSheet(next)).finally(() => setMorphing(false))
  }, [])

  const toggleSheet = useCallback(
    (instant = false) => void resize((size) => FLIPPED[size], instant),
    [resize],
  )

  const covering = compact && sheet === "full"
  const reveal = useCallback(() => {
    if (!covering) return
    const anchor = document.activeElement
    void resize(() => "half", false).then(() => keepInView(anchor))
  }, [covering, resize])

  useEffect(() => {
    if (sheet === "full" && (!compact || phase === "closed")) setSheet("half")
  }, [compact, phase, sheet])

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

  return {
    width,
    phase,
    sheet,
    compact,
    morphing,
    covering: covering && phase === "open",
    collapseBelow,
    collapse,
    expand,
    settle,
    toggle,
    toggleSheet,
    reveal,
  }
}

export type PanelDockState = ReturnType<typeof usePanelDock>
export type DockToggleState = PanelDockState["toggle"]
