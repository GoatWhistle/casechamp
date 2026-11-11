import { clsx } from "clsx"
import type { ReactNode } from "react"
import styles from "./fact-list.module.css"

export interface FactItem {
  readonly key: string
  readonly value: ReactNode
  readonly label: string
}

export interface FactListProps {
  readonly items: readonly FactItem[]
  readonly label: string
  readonly className?: string | undefined
}

export function FactList({ items, label, className }: FactListProps) {
  return (
    <ul className={clsx(styles.facts, className)} aria-label={label}>
      {items.map((item) => (
        <li key={item.key} className={styles.fact}>
          <span className={styles.value}>{item.value}</span>
          <span className={styles.label}>{item.label}</span>
        </li>
      ))}
    </ul>
  )
}
