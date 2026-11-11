import { type RefObject, useLayoutEffect } from "react"
import { readPixels } from "@/shared/motion"
import styles from "./hover-card.module.css"

export interface HoverCardRow {
  readonly key: string
  readonly label: string
  readonly value: string | null
}

export interface HoverCardProps {
  readonly cardRef: RefObject<HTMLDivElement | null>
  readonly point: RefObject<{ x: number; y: number }>
  readonly title: string
  readonly rows: readonly HoverCardRow[]
  readonly none: string
}

export function placeHoverCard(card: HTMLDivElement, x: number, y: number) {
  const area = card.parentElement?.getBoundingClientRect()
  const gap = readPixels("--space-16", card)
  card.style.transform = `translate(${x}px, ${y}px)`
  card.dataset.flip = String(area !== undefined && x + gap + card.offsetWidth > area.right - gap)
  card.dataset.below = String(area !== undefined && y - gap - card.offsetHeight < area.top + gap)
}

export function HoverCard({ cardRef, point, title, rows, none }: HoverCardProps) {
  useLayoutEffect(() => {
    if (cardRef.current) placeHoverCard(cardRef.current, point.current.x, point.current.y)
  })
  return (
    <div className={styles.hover} ref={cardRef} aria-hidden="true">
      <b className={styles.hoverTitle}>{title}</b>
      {rows.map((row) => (
        <span key={row.key} className={styles.hoverRow}>
          <span>{row.label}</span>
          <span className={styles.hoverValue}>{row.value ?? none}</span>
        </span>
      ))}
    </div>
  )
}
