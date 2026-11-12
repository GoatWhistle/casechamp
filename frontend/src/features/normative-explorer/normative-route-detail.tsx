import { useNormativeRoute } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { useTranslation } from "@/shared/i18n"
import { ErrorState, StatusBadge } from "@/shared/ui"
import styles from "./normative-panel.module.css"

export function NormativeRouteDetail({
  runId,
  originId,
  stage,
  regional = false,
}: {
  readonly regional?: boolean
  readonly runId: string
  readonly originId: string
  readonly stage: NormativeRouteStage
}) {
  const { t } = useTranslation()
  const route = useNormativeRoute(runId, originId, stage, regional)
  if (route.isPending)
    return <StatusBadge tone="neutral" icon="route" label={t("normative:routePending")} />
  if (route.isError)
    return (
      <ErrorState
        title={t("normative:routeError")}
        description={t("normative:routeRecalculate")}
        onRetry={() => void route.refetch()}
      />
    )
  return (
    <div>
      <StatusBadge tone="info" icon="route" label={t("normative:routeShown")} />
      <p className={styles.explanation}>{t("normative:routeApproaches")}</p>
    </div>
  )
}
