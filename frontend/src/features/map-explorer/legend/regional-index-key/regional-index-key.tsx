import type { ReactNode } from "react"
import { useRegionalIndexMap } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ErrorState } from "@/shared/ui"
import styles from "./regional-index-key.module.css"

export function RegionalIndexKey({
  criterionId,
  stage,
  children,
}: {
  readonly criterionId: string
  readonly stage: NormativeRouteStage
  readonly children: ReactNode
}) {
  const query = useRegionalIndexMap(criterionId, stage)
  const { t } = useTranslation()
  const f = useFormatters()
  const weighting = query.data?.[0]?.weighting
  return (
    <div className={styles.key}>
      <p>
        {t(
          weighting === "population"
            ? "normative:indexPopulationBasis"
            : "normative:indexPointBasis",
        )}
      </p>
      <p>{t("normative:indexMinimumVariant")}</p>
      <p>{t("normative:indexScenarioMapNote")}</p>
      {query.data?.some((row) => row.data_source === "archived_aggregate") ? (
        <p>{t("normative:archive.summary")}</p>
      ) : null}
      {query.isError ? (
        <ErrorState title={t("normative:loadError")} onRetry={() => void query.refetch()} />
      ) : (
        children
      )}
      {query.data ? (
        <p>
          {t("normative:indexReadyCount", {
            count: f.integer(query.data.filter((row) => row.value_min !== null).length),
            total: f.integer(query.data.length),
          })}
        </p>
      ) : null}
    </div>
  )
}
