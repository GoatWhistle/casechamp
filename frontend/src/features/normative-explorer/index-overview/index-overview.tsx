import { type IndexMapRegion, useRegionalIndexMap } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { type MessageKey, useFormatters, useTranslation } from "@/shared/i18n"
import {
  Card,
  DataTable,
  ErrorState,
  NoValue,
  ScrollArea,
  Skeleton,
  StatusBadge,
} from "@/shared/ui"
import styles from "./index-overview.module.css"

const STATUS_KEYS: Readonly<Record<string, MessageKey>> = {
  ready: "normative:indexStatuses.ready",
  scenario_ready: "normative:indexStatuses.scenarioReady",
  basis_missing: "normative:indexStatuses.basisMissing",
  measurement_missing: "normative:indexStatuses.measurementMissing",
  unpublished: "normative:indexStatuses.unpublished",
  model_unavailable: "normative:indexStatuses.modelUnavailable",
  measurement_incompatible: "normative:indexStatuses.measurementIncompatible",
  not_regulated: "normative:indexStatuses.notRegulated",
  local_selection_required: "normative:indexStatuses.localSelectionRequired",
  population_unknown: "normative:indexStatuses.populationUnknown",
}

export function IndexOverview({
  criterionId,
  stage,
  onRegion,
}: {
  readonly criterionId: string
  readonly stage: NormativeRouteStage
  readonly onRegion?: ((id: string) => void) | undefined
}) {
  const query = useRegionalIndexMap(criterionId, stage)
  const { t } = useTranslation()
  const f = useFormatters()
  const value = (row: IndexMapRegion) =>
    row.value_min === null ? (
      <NoValue />
    ) : row.value_max !== row.value_min && row.value_max !== null ? (
      t("normative:indexRange", {
        min: f.number(row.value_min, 1),
        max: f.number(row.value_max, 1),
      })
    ) : (
      f.percent(row.value_min / 100, 1)
    )
  return (
    <ScrollArea className={styles.scroll} label={t("normative:resultRegion")}>
      <Card as="div" className={styles.overview} title={t("normative:indexOverviewTitle")}>
        <StatusBadge tone="warning" label={t("normative:indexConditional")} />
        <p>{t("normative:indexOverviewNote")}</p>
        <p>{t("normative:indexScenarioMapNote")}</p>
        {query.isPending ? (
          <Skeleton lines={6} />
        ) : query.isError ? (
          <ErrorState title={t("normative:loadError")} onRetry={() => void query.refetch()} />
        ) : (
          <>
            <p>
              {t("normative:indexReadyCount", {
                count: f.integer(query.data.filter((row) => row.value_min !== null).length),
                total: f.integer(query.data.length),
              })}
            </p>
            <DataTable<IndexMapRegion>
              caption={t("normative:indexOverviewTitle")}
              rows={query.data}
              rowKey={(row) => row.region_id}
              pageSize={20}
              onRowClick={onRegion ? (row) => onRegion(row.region_id) : undefined}
              defaultSort={{ key: "index", direction: "descending" }}
              columns={[
                {
                  key: "region",
                  header: t("normative:indexRegion"),
                  sortValue: (row) => row.region_name,
                  cell: (row) => (
                    <div className={styles.region}>
                      <span>{row.region_name}</span>
                      <span className={styles.status}>
                        {t(STATUS_KEYS[row.status] ?? "normative:indexStatuses.unpublished")}
                      </span>
                    </div>
                  ),
                },
                {
                  key: "index",
                  header: t("normative:indexColumn"),
                  numeric: true,
                  sortValue: (row) => row.value_min,
                  cell: value,
                },
              ]}
            />
          </>
        )}
      </Card>
    </ScrollArea>
  )
}
