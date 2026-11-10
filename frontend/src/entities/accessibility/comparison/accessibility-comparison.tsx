import { useState } from "react"
import { useTranslation } from "@/shared/i18n"
import { Banner, Card, ErrorState, Segmented, Skeleton } from "@/shared/ui"
import { type HalfLife, useAccessibility } from "../accessibility.queries"
import styles from "./accessibility-comparison.module.css"
import { ComparisonTables } from "./comparison-tables"

export interface AccessibilityComparisonProps {
  readonly regionId: string
}

export function AccessibilityComparison({ regionId }: AccessibilityComparisonProps) {
  const { t } = useTranslation()
  const [halfLife, setHalfLife] = useState<HalfLife>("2")
  const query = useAccessibility(regionId, halfLife)
  const data = query.data
  const options = (["2", "4", "8"] as const).map((value) => ({
    value,
    label: t("accessibility:hours", { count: Number(value) }),
  }))
  return (
    <Card
      as="section"
      title={t("accessibility:title")}
      actions={
        <Segmented
          label={t("accessibility:halfLife")}
          options={options}
          value={halfLife}
          onChange={setHalfLife}
        />
      }
    >
      <div className={styles.comparison}>
        <p className={styles.explanation}>{t("accessibility:description")}</p>
        {halfLife !== "2" ? <Banner tone="info" title={t("accessibility:sensitivity")} /> : null}
        {query.isError ? (
          <ErrorState title={t("accessibility:unavailable")} onRetry={() => void query.refetch()} />
        ) : data ? (
          <>
            {!data.source_current ? (
              <Banner tone="warning" title={t("accessibility:stale")} />
            ) : null}
            <ComparisonTables data={data} />
            <p className={styles.provenance}>
              {t("accessibility:source", {
                model: data.run.model_version,
                source: data.run.source_artifact,
              })}
            </p>
            <p className={styles.provenance}>
              {t(
                data.run.normalization_kind === "legacy_multimodal_road"
                  ? "accessibility:legacyScale"
                  : "accessibility:roadScale",
              )}
            </p>
          </>
        ) : (
          <Skeleton lines={8} />
        )}
      </div>
    </Card>
  )
}
