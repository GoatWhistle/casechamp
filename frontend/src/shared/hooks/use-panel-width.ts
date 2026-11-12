import { type RefObject, useCallback, useLayoutEffect, useState } from "react"
import { readPixels } from "@/shared/motion"

const MAX_SHARE = 0.6

interface PanelWidthOptions {
  readonly minToken?: `--${string}`
  readonly baseToken?: `--${string}`
  readonly maxToken?: `--${string}`
  readonly maxShare?: number
}

function stored(key: string): number | null {
  try {
    const value = Number(localStorage.getItem(key))
    return Number.isFinite(value) && value > 0 ? value : null
  } catch {
    return null
  }
}

function save(key: string, width: number | null) {
  try {
    if (width === null) localStorage.removeItem(key)
    else localStorage.setItem(key, String(width))
  } catch {
    return
  }
}

export function usePanelWidth(
  host: RefObject<HTMLElement | null>,
  key: string,
  {
    minToken = "--panel-min",
    baseToken = "--map-panel-width",
    maxToken = "--map-panel-max",
    maxShare = MAX_SHARE,
  }: PanelWidthOptions = {},
) {
  const [width, setWidth] = useState<number | null>(() => stored(key))
  const [bounds, setBounds] = useState({ min: 320, max: 760, base: 400 })

  useLayoutEffect(() => {
    const element = host.current
    if (!element) return
    const measure = () => {
      const min = Math.min(readPixels(minToken, element), element.clientWidth)
      const base = readPixels(baseToken, element)
      const cap = readPixels(maxToken, element)
      const max = Math.max(min, Math.min(cap, element.clientWidth * maxShare))
      setBounds({ min, max, base })
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [host, minToken, baseToken, maxToken, maxShare])

  const current = Math.min(bounds.max, Math.max(bounds.min, width ?? bounds.base))

  const preview = useCallback(
    (next: number) => host.current?.style.setProperty("--panel-size", String(next)),
    [host],
  )

  const commit = useCallback(
    (next: number) => {
      host.current?.style.removeProperty("--panel-size")
      setWidth(next)
      save(key, next)
    },
    [host, key],
  )

  const reset = useCallback(() => {
    host.current?.style.removeProperty("--panel-size")
    setWidth(null)
    save(key, null)
  }, [host, key])

  return { width: current, ...bounds, preview, commit, reset }
}
