import {
  NetworkModeControl,
  type RegionSummary,
  SeasonControl,
  useRegions,
} from "@/entities/region"
import { useSeason } from "@/shared/hooks/use-season"
import { useErrorText, useTranslation } from "@/shared/i18n"
import { Button, EmptyState, ErrorState, Skeleton } from "@/shared/ui"
import { MetricBoard } from "./metric-board"
import styles from "./region-compare.module.css"
import { RegionPicker } from "./region-picker"
import { useCompareParams } from "./use-compare-params"

function extremes(regions: readonly RegionSummary[]): RegionSummary[] {
  const ranked = regions
    .filter((region) => region.hansen !== null)
    .sort((a, b) => (b.hansen ?? 0) - (a.hansen ?? 0))
  const first = ranked.at(0)
  const last = ranked.at(-1)
  if (first === undefined || last === undefined) return []
  return first.id === last.id ? [first] : [first, last]
}

export function RegionCompare() {
  const { t } = useTranslation()
  const errorText = useErrorText()
  const { season } = useSeason()
  const regions = useRegions(season)
  const { ids, add, remove } = useCompareParams()
  if (regions.isError)
    return (
      <ErrorState
        title={t("compare:loadError")}
        description={errorText(regions.error)}
        onRetry={() => void regions.refetch()}
      />
    )
  if (!regions.data) return <Skeleton lines={10} />
  const rows = ids
    .map((id) => (regions.data ?? []).find((region) => region.id === id))
    .filter((region): region is NonNullable<typeof region> => region !== undefined)
  return (
    <div className={styles.compare}>
      <div className={styles.controls}>
        <RegionPicker regions={regions.data} ids={ids} onAdd={add} onRemove={remove} />
        <div className={styles.modes}>
          <SeasonControl />
          <NetworkModeControl />
        </div>
      </div>
      {rows.length === 0 ? (
        <EmptyState
          icon="compare"
          title={t("compare:empty")}
          description={t("compare:emptyHint")}
          action={
            <div className={styles.suggestions}>
              {extremes(regions.data).map((region) => (
                <Button
                  key={region.id}
                  variant="secondary"
                  size="compact"
                  icon="plus"
                  onClick={() => add(region.id)}
                >
                  {t("compare:suggest", { name: region.name })}
                </Button>
              ))}
            </div>
          }
        />
      ) : (
        <MetricBoard rows={rows} />
      )}
    </div>
  )
}
