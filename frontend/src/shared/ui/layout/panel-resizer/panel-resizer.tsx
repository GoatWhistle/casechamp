import clsx from "clsx"
import { type KeyboardEvent, type PointerEvent, useRef } from "react"
import styles from "./panel-resizer.module.css"

export interface PanelResizerProps {
  readonly width: number
  readonly min: number
  readonly max: number
  readonly label: string
  readonly onPreview: (width: number) => void
  readonly onCommit: (width: number) => void
  readonly onReset: () => void
  readonly className?: string | undefined
  readonly edge?: "start" | "end"
  readonly controls?: string | undefined
  readonly grip?: boolean
}

const STEP = 16
const LARGE_STEP = 64

function keyTarget(
  event: KeyboardEvent<HTMLDivElement>,
  width: number,
  min: number,
  max: number,
  direction: number,
): number | null {
  const step = event.shiftKey ? LARGE_STEP : STEP
  const targets: Readonly<Record<string, number>> = {
    ArrowLeft: width - step * direction,
    ArrowRight: width + step * direction,
    Home: min,
    End: max,
  }
  return targets[event.key] ?? null
}

interface Drag {
  readonly id: number
  readonly startX: number
  readonly startWidth: number
  width: number
}

export function PanelResizer({
  width,
  min,
  max,
  label,
  onPreview,
  onCommit,
  onReset,
  className,
  edge = "start",
  controls,
  grip = false,
}: PanelResizerProps) {
  const drag = useRef<Drag | null>(null)
  const frame = useRef<number | null>(null)
  const clamp = (value: number) => Math.round(Math.min(max, Math.max(min, value)))
  const direction = edge === "end" ? 1 : -1

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0 || drag.current !== null) return
    event.preventDefault()
    event.currentTarget.setPointerCapture(event.pointerId)
    drag.current = { id: event.pointerId, startX: event.clientX, startWidth: width, width }
  }

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const state = drag.current
    if (!state || state.id !== event.pointerId) return
    state.width = clamp(state.startWidth + (event.clientX - state.startX) * direction)
    if (frame.current !== null) return
    frame.current = requestAnimationFrame(() => {
      frame.current = null
      if (drag.current) onPreview(drag.current.width)
    })
  }

  const finish = (event: PointerEvent<HTMLDivElement>) => {
    const state = drag.current
    if (!state || state.id !== event.pointerId) return
    drag.current = null
    if (frame.current !== null) cancelAnimationFrame(frame.current)
    frame.current = null
    onCommit(state.width)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const next = keyTarget(event, width, min, max, direction)
    if (next === null) return
    event.preventDefault()
    onCommit(clamp(next))
  }

  return (
    // biome-ignore lint/a11y/useSemanticElements: a focusable separator is the ARIA pattern for a resizable splitter; <hr> cannot take focus or keyboard input
    <div
      className={clsx(styles.resizer, className)}
      data-grip={grip || undefined}
      role="separator"
      tabIndex={0}
      aria-orientation="vertical"
      aria-label={label}
      aria-controls={controls}
      aria-valuenow={width}
      aria-valuemin={min}
      aria-valuemax={max}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={finish}
      onPointerCancel={finish}
      onDoubleClick={onReset}
      onKeyDown={onKeyDown}
    >
      <span className={styles.grip} aria-hidden="true" />
    </div>
  )
}
