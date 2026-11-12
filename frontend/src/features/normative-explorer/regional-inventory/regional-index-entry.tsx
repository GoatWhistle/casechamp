import { ArchiveNotice, type IndexMapRegion, useRegionalIndexMap } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Card, ErrorState, NoValue, Skeleton, Stat } from "@/shared/ui"
import { RegionalIndexCard as LiveRegionalIndexCard } from "./regional-index-card"

export function RegionalIndexCard(props: {
  readonly regionId: string
  readonly criterionId: string
  readonly runId?: string | undefined
  readonly stage: NormativeRouteStage
}) {
  const map = useRegionalIndexMap(props.criterionId, props.stage)
  const { t } = useTranslation()
  if (map.isPending) return <Skeleton lines={4} />
  if (map.isError)
    return <ErrorState title={t("normative:loadError")} onRetry={() => void map.refetch()} />
  const row = map.data.find((value) => value.region_id === props.regionId)
  return row?.data_source === "archived_aggregate" ? (
    <ArchivedIndex row={row} />
  ) : (
    <LiveRegionalIndexCard {...props} />
  )
}

function ArchivedIndex({ row }: { readonly row: IndexMapRegion }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const value =
    row.value_min === null ? (
      <NoValue />
    ) : row.value_max !== null && row.value_max !== row.value_min ? (
      t("normative:indexRange", {
        min: f.number(row.value_min, 1),
        max: f.number(row.value_max, 1),
      })
    ) : (
      f.percent(row.value_min / 100, 1)
    )
  return (
    <Card as="div" title={t("normative:indexTitle")}>
      <Stat label={row.region_name} value={value} />
      <ArchiveNotice row={row} />
    </Card>
  )
}
