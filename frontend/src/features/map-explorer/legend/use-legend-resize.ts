import {
  type KeyboardEvent,
  type PointerEvent,
  type RefObject,
  useEffect,
  useRef,
  useState,
} from "react"
import type { usePanelWidth } from "@/shared/hooks"

interface Size {
  readonly width: number
  readonly height: number
}

interface Drag {
  readonly id: number
  readonly x: number
  readonly y: number
  readonly origin: Size
  readonly savedHeight: number | null
  readonly minHeight: number
  readonly maxHeight: number
  next: Size
}

const HEIGHT_KEY = "plexus.map-legend-height"

function storedHeight(): number | null {
  try {
    const value = Number(localStorage.getItem(HEIGHT_KEY))
    return Number.isFinite(value) && value > 0 ? value : null
  } catch {
    return null
  }
}

function saveHeight(height: number | null) {
  try {
    if (height === null) localStorage.removeItem(HEIGHT_KEY)
    else localStorage.setItem(HEIGHT_KEY, String(height))
  } catch {
    return
  }
}

export function useLegendResize(
  panel: RefObject<HTMLElement | null>,
  width: ReturnType<typeof usePanelWidth>,
) {
  const [height, setHeight] = useState(storedHeight)
  const drag = useRef<Drag | null>(null)
  const frame = useRef<number | null>(null)

  const cancelFrame = () => {
    if (frame.current !== null) cancelAnimationFrame(frame.current)
    frame.current = null
  }

  useEffect(
    () => () => {
      if (frame.current !== null) cancelAnimationFrame(frame.current)
    },
    [],
  )

  const applyHeight = (next: number | null) => {
    if (panel.current) panel.current.style.blockSize = next === null ? "" : `${next}px`
    setHeight(next)
    saveHeight(next)
  }

  const clamp = (size: Size, minHeight: number, maxHeight: number): Size => ({
    width: Math.round(Math.max(width.min, Math.min(width.max, size.width))),
    height: Math.round(Math.max(minHeight, Math.min(maxHeight, size.height))),
  })

  const reset = () => {
    width.reset()
    applyHeight(null)
  }

  const onPointerDown = (event: PointerEvent<HTMLButtonElement>) => {
    const element = panel.current
    if (!element || event.button !== 0 || drag.current) return
    event.preventDefault()
    event.currentTarget.focus({ preventScroll: true })
    event.currentTarget.setPointerCapture(event.pointerId)
    const style = getComputedStyle(element)
    const origin = { width: width.width, height: element.offsetHeight }
    drag.current = {
      id: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      origin,
      savedHeight: height,
      minHeight: Number.parseFloat(style.minBlockSize),
      maxHeight: Number.parseFloat(style.maxBlockSize),
      next: origin,
    }
  }

  const onPointerMove = (event: PointerEvent<HTMLButtonElement>) => {
    const state = drag.current
    if (!state || state.id !== event.pointerId) return
    state.next = clamp(
      {
        width: state.origin.width + event.clientX - state.x,
        height: state.origin.height + state.y - event.clientY,
      },
      state.minHeight,
      state.maxHeight,
    )
    if (frame.current !== null) return
    frame.current = requestAnimationFrame(() => {
      frame.current = null
      if (!drag.current) return
      width.preview(drag.current.next.width)
      if (panel.current) panel.current.style.blockSize = `${drag.current.next.height}px`
    })
  }

  const finish = (element: HTMLButtonElement, cancel = false) => {
    const state = drag.current
    if (!state) return
    drag.current = null
    cancelFrame()
    width.commit(cancel ? state.origin.width : state.next.width)
    applyHeight(cancel ? state.savedHeight : state.next.height)
    if (element.hasPointerCapture(state.id)) element.releasePointerCapture(state.id)
  }

  const onPointerUp = (event: PointerEvent<HTMLButtonElement>) => {
    if (drag.current?.id === event.pointerId) finish(event.currentTarget)
  }

  const onPointerCancel = (event: PointerEvent<HTMLButtonElement>) => {
    if (drag.current?.id === event.pointerId) finish(event.currentTarget, true)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Escape" && drag.current) {
      event.preventDefault()
      finish(event.currentTarget, true)
      return
    }
    if (drag.current || !panel.current) return
    if (event.key === "Home") {
      event.preventDefault()
      reset()
      return
    }
    const step = event.shiftKey ? 64 : 16
    const currentHeight = panel.current.offsetHeight
    const targets: Readonly<Record<string, Size>> = {
      ArrowLeft: { width: width.width - step, height: currentHeight },
      ArrowRight: { width: width.width + step, height: currentHeight },
      ArrowUp: { width: width.width, height: currentHeight + step },
      ArrowDown: { width: width.width, height: currentHeight - step },
    }
    const target = targets[event.key]
    if (!target) return
    event.preventDefault()
    const style = getComputedStyle(panel.current)
    const next = clamp(
      target,
      Number.parseFloat(style.minBlockSize),
      Number.parseFloat(style.maxBlockSize),
    )
    width.commit(next.width)
    applyHeight(next.height)
  }

  return {
    height: height ?? undefined,
    handlers: {
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPointerCancel,
      onLostPointerCapture: onPointerUp,
      onKeyDown,
      onDoubleClick: reset,
    },
  }
}
