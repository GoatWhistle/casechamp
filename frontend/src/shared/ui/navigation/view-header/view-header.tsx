import type { ReactNode } from "react"
import { Tooltip } from "../../overlays/tooltip/tooltip"
import { Button } from "../../primitives/button/button"
import styles from "./view-header.module.css"

export interface ViewHeaderProps {
  readonly title: string
  readonly backLabel: string
  readonly onBack: () => void
  readonly aside?: ReactNode
}

export function ViewHeader({ title, backLabel, onBack, aside }: ViewHeaderProps) {
  return (
    <header className={styles.header}>
      <Tooltip content={backLabel} describe={false}>
        <Button
          variant="ghost"
          size="compact"
          icon="arrow-left"
          aria-label={backLabel}
          className={styles.back}
          onClick={onBack}
        >
          {null}
        </Button>
      </Tooltip>
      <h2 className={styles.title}>{title}</h2>
      {aside === undefined ? null : <div className={styles.aside}>{aside}</div>}
    </header>
  )
}
