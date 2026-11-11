import { useFormatters, useTranslation } from "@/shared/i18n"
import { Card } from "@/shared/ui"
import type { Mode } from "../link.queries"
import { sharesOfTotals } from "../link-modes"
import { ModeBar } from "../mode-bar/mode-bar"
import { ModeLegend } from "../mode-legend/mode-legend"
import styles from "./region-links.module.css"

export interface ModeTotalsProps {
  readonly totals: Readonly<Record<Mode, number>>
  readonly total: number
  readonly className?: string | undefined
}

export function ModeTotals({ totals, total, className }: ModeTotalsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const shares = sharesOfTotals(totals)
  return (
    <Card
      as="section"
      title={t("data:metric.links")}
      className={className}
      actions={<span className={styles.total}>{f.integer(total)}</span>}
    >
      <ModeBar rows={shares} />
      <ModeLegend rows={shares} label={t("links:groups")} />
    </Card>
  )
}
