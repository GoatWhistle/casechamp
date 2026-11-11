import clsx from "clsx"
import type { CSSProperties } from "react"
import styles from "./chat-mark.module.css"

export interface ChatMarkProps {
  readonly rings?: 1 | 2 | 3
  readonly motion?: "none" | "pulse"
  readonly className?: string | undefined
}

const BUBBLE =
  "M34 24H66A14 14 0 0 1 80 38V54A14 14 0 0 1 66 68H48L31 80L34 68A14 14 0 0 1 20 54V38A14 14 0 0 1 34 24Z"
const DOTS = [38, 50, 62] as const
const OFFSETS = [8, 16, 24] as const
const LINE = 3.2

export function ChatMark({ rings = 2, motion = "none", className }: ChatMarkProps) {
  const offsets = OFFSETS.slice(0, rings).reverse()
  return (
    <svg className={clsx(styles.mark, className)} viewBox="-8 -4 116 112" aria-hidden="true">
      {offsets.map((offset) => (
        <g
          key={offset}
          data-ring={OFFSETS.indexOf(offset) + 1}
          className={motion === "pulse" ? styles.pulse : undefined}
          style={{ "--i": OFFSETS.indexOf(offset) } as CSSProperties}
        >
          <path className={styles.band} d={BUBBLE} strokeWidth={(offset + LINE / 2) * 2} />
          <path className={styles.cut} d={BUBBLE} strokeWidth={(offset - LINE / 2) * 2} />
        </g>
      ))}
      <path className={styles.bubble} d={BUBBLE} />
      {DOTS.map((x) => (
        <circle key={x} className={styles.dot} cx={x} cy={46} r={4.5} />
      ))}
    </svg>
  )
}
