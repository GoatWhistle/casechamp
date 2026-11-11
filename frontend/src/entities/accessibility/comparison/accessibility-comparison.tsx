import { useState } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, Card, Disclosure, ErrorState, Segmented, Skeleton } from "@/shared/ui"
import { type ComparisonData, type HalfLife, useAccessibility } from "../accessibility.queries"
import styles from "./accessibility-comparison.module.css"
import { ComparisonTables } from "./comparison-tables"

export interface AccessibilityComparisonProps {
  readonly regionId: string
}

const ARTIFACT_DATE = /(\d{4})(\d{2})(\d{2})/

function artifactDate(artifact: string): string | null {
  const match = ARTIFACT_DATE.exec(artifact)
  return match === null ? null : `${match[1]}-${match[2]}-${match[3]}`
}

function Method({ data }: { readonly data: ComparisonData }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const date = artifactDate(data.run.source_artifact)
  return (
    <Disclosure title={t("accessibility:method")} className={styles.method}>
      <div className={styles.methodBody}>
        <p>{t("accessibility:description")}</p>
        <p>
          {t(
            data.run.normalization_kind === "legacy_multimodal_road"
              ? "accessibility:legacyScale"
              : "accessibility:roadScale",
          )}
        </p>
        {date === null ? null : <p>{t("accessibility:snapshot", { date: f.date(date) })}</p>}
      </div>
    </Disclosure>
  )
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
      description={t("accessibility:lead")}
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
        {halfLife !== "2" ? <Banner tone="info" title={t("accessibility:sensitivity")} /> : null}
        {query.isError ? (
          <ErrorState title={t("accessibility:unavailable")} onRetry={() => void query.refetch()} />
        ) : data ? (
          <>
            {!data.source_current ? (
              <Banner tone="warning" title={t("accessibility:stale")} />
            ) : null}
            <ComparisonTables data={data} />
            <Method data={data} />
          </>
        ) : (
          <Skeleton lines={8} />
        )}
      </div>
    </Card>
  )
}
