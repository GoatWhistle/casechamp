import { clsx } from "clsx"
import type { CSSProperties } from "react"
import type { Mode } from "../link.queries"
import styles from "./mode-swatch.module.css"

export type ModeSwatchShape = "chip" | "fill"

const SHAPE_CLASS: Readonly<Record<ModeSwatchShape, string | undefined>> = {
  chip: styles.chip,
  fill: styles.fill,
}

export interface ModeSwatchProps {
  readonly mode: Mode | null
  readonly shape?: ModeSwatchShape
  readonly model?: boolean
  readonly className?: string | undefined
  readonly style?: CSSProperties | undefined
}

export function ModeSwatch({
  mode,
  shape = "chip",
  model = false,
  className,
  style,
}: ModeSwatchProps) {
  return (
    <i
      className={clsx(styles.swatch, SHAPE_CLASS[shape], model && styles.model, className)}
      data-mode={mode ?? "neutral"}
      style={style}
      aria-hidden="true"
    />
  )
}
