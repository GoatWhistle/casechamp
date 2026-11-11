import type { CSSProperties } from "react"
import styles from "./meter.module.css"

export interface MeterProps {
  readonly value: number | null
  readonly max: number
  readonly label: string
  readonly thin?: boolean
}

export function Meter({ value, max, label, thin = false }: MeterProps) {
  if (!thin)
    return (
      <progress className={styles.meter} value={value ?? undefined} max={max} aria-label={label} />
    )
  const ratio = value === null ? 1 : Math.min(1, Math.max(0, value / Math.max(1, max)))
  return (
    <div
      className={styles.thin}
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value ?? undefined}
      data-pending={value === null}
    >
      <span className={styles.fill} style={{ "--meter-progress": ratio } as CSSProperties} />
    </div>
  )
}
