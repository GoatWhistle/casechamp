import { useFormatters, useTranslation } from "@/shared/i18n"
import type { ModeShare } from "../link-modes"
import { ModeSwatch } from "../mode-swatch/mode-swatch"
import styles from "./mode-legend.module.css"

export interface ModeLegendProps {
  readonly rows: readonly ModeShare[]
  readonly label: string
}

export function ModeLegend({ rows, label }: ModeLegendProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <ul className={styles.legend} aria-label={label}>
      {rows.map((row) => (
        <li key={row.mode} className={styles.row}>
          <ModeSwatch mode={row.mode} />
          <span className={styles.name}>{t(`data:mode.${row.mode}`)}</span>
          <span className={styles.count}>{f.integer(row.count)}</span>
        </li>
      ))}
    </ul>
  )
}
