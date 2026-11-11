import { clsx } from "clsx"
import type { CSSProperties } from "react"
import type { Mode } from "../link.queries"
import type { ModeShare } from "../link-modes"
import { ModeSwatch } from "../mode-swatch/mode-swatch"
import styles from "./mode-bar.module.css"

export interface ModeBarProps {
  readonly rows: readonly ModeShare[]
  readonly active?: Mode | null
  readonly className?: string | undefined
}

function grow(value: number): CSSProperties {
  return { "--n": value } as CSSProperties
}

export function ModeBar({ rows, active = null, className }: ModeBarProps) {
  return (
    <div
      className={clsx(styles.bar, className)}
      data-active={active === null ? undefined : ""}
      aria-hidden="true"
    >
      {rows.map((row) => (
        <span
          key={row.mode}
          className={styles.segment}
          data-on={row.mode === active || undefined}
          style={grow(row.count)}
        >
          {row.count > row.model ? (
            <ModeSwatch
              mode={row.mode}
              shape="fill"
              className={styles.part}
              style={grow(row.count - row.model)}
            />
          ) : null}
          {row.model > 0 ? (
            <ModeSwatch
              mode={row.mode}
              shape="fill"
              model
              className={styles.part}
              style={grow(row.model)}
            />
          ) : null}
        </span>
      ))}
    </div>
  )
}
