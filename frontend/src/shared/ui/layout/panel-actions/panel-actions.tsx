import type { ReactNode } from "react"
import styles from "./panel-actions.module.css"

export function PanelActions({ children }: { readonly children: ReactNode }) {
  return <div className={styles.actions}>{children}</div>
}
