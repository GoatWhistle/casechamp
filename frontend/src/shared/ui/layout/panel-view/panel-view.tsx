import type { ReactNode } from "react"
import { ScrollArea } from "../scroll-area/scroll-area"
import styles from "./panel-view.module.css"

export interface PanelViewProps {
  readonly label: string
  readonly header?: ReactNode
  readonly footer?: ReactNode
  readonly children: ReactNode
}

export function PanelView({ label, header, footer, children }: PanelViewProps) {
  return (
    <div className={styles.view}>
      {header === undefined ? null : <div className={styles.header}>{header}</div>}
      <ScrollArea className={styles.body} label={label}>
        <div className={styles.content}>{children}</div>
      </ScrollArea>
      {footer === undefined ? null : <div className={styles.footer}>{footer}</div>}
    </div>
  )
}
