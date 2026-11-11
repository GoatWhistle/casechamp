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

interface Placement {
  readonly area: DOMRect | undefined
  readonly gap: number
  readonly width: number
  readonly height: number
}

const placements = new WeakMap<HTMLElement, Placement>()

export function measureHoverCard(card: HTMLDivElement) {
  const area = card.parentElement?.getBoundingClientRect()
  const gap = readPixels("--space-16", card)
  const width = card.offsetWidth
  const height = card.offsetHeight
  const placement = { area, gap, width, height }
  placements.set(card, placement)
  return placement
}

export function placeHoverCard(card: HTMLDivElement, x: number, y: number) {
  const { area, gap, width, height } = placements.get(card) ?? measureHoverCard(card)
  const flip = String(area !== undefined && x + gap + width > area.right - gap)
  const below = String(area !== undefined && y - gap - height < area.top + gap)
  card.style.transform = `translate(${x}px, ${y}px)`
  if (card.dataset.flip !== flip) card.dataset.flip = flip
  if (card.dataset.below !== below) card.dataset.below = below
}

export function HoverCard({ cardRef, point, title, rows, none }: HoverCardProps) {
  useLayoutEffect(() => {
    const card = cardRef.current
    if (!card) return
    const measure = () => {
      measureHoverCard(card)
      placeHoverCard(card, point.current.x, point.current.y)
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(card)
    if (card.parentElement) observer.observe(card.parentElement)
    window.addEventListener("scroll", measure, true)
    return () => {
      observer.disconnect()
      window.removeEventListener("scroll", measure, true)
      placements.delete(card)
    }
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
