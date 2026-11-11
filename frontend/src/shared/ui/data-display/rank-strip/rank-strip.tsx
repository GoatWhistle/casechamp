import { clsx } from "clsx"
import type { CSSProperties, ReactNode } from "react"
import styles from "./rank-strip.module.css"

export interface RankStripMark {
  readonly value: number
  readonly label: string
}

export interface RankStripProps {
  readonly values: readonly number[]
  readonly current: number
  readonly label: string
  readonly lowLabel: string
  readonly highLabel: string
  readonly currentLabel?: ReactNode
  readonly median?: RankStripMark | undefined
  readonly className?: string | undefined
}

function position(value: number, min: number, max: number): number {
  if (max <= min) return 0.5
  return (value - min) / (max - min)
}

function dotKeys(values: readonly number[]): readonly [string, number][] {
  const seen = new Map<number, number>()
  return values.map((value) => {
    const count = seen.get(value) ?? 0
    seen.set(value, count + 1)
    return [`${value}-${count}`, value]
  })
}

function at(x: number): CSSProperties {
  return { "--x": x } as CSSProperties
}

export function RankStrip({
  values,
  current,
  label,
  lowLabel,
  highLabel,
  currentLabel,
  median,
  className,
}: RankStripProps) {
  const min = Math.min(current, ...values)
  const max = Math.max(current, ...values)
  const x = position(current, min, max)
  return (
    <figure className={clsx(styles.strip, className)}>
      <figcaption className="visually-hidden">{label}</figcaption>
      {currentLabel === undefined ? null : (
        <span className={styles.current} style={at(x)}>
          {currentLabel}
        </span>
      )}
      <span className={styles.track} aria-hidden="true">
        {dotKeys(values).map(([key, value]) => (
          <i key={key} className={styles.dot} style={at(position(value, min, max))} />
        ))}
        {median === undefined ? null : (
          <i className={styles.median} style={at(position(median.value, min, max))} />
        )}
        <i className={styles.marker} style={at(x)} />
      </span>
      <span className={styles.ends} aria-hidden="true">
        <span>{lowLabel}</span>
        {median === undefined ? null : (
          <span className={styles.medianLabel} style={at(position(median.value, min, max))}>
            {median.label}
          </span>
        )}
        <span>{highLabel}</span>
      </span>
    </figure>
  )
}
