import type { Overview } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Card, FactList } from "@/shared/ui"
import styles from "./region-summary.module.css"
import { useSummaryFacts } from "./summary-facts"

export interface CountrySummaryProps {
  readonly overview: Overview
}

export function CountryOverview({ overview }: CountrySummaryProps) {
  const { t } = useTranslation()
  const facts = useSummaryFacts(overview)
  return (
    <Card
      as="section"
      title={<span className={styles.name}>{t("map:overview.title")}</span>}
      className={styles.overview}
    >
      <FactList items={facts} label={t("map:facts.label")} />
    </Card>
  )
}
