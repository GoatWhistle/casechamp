import { memo, type ReactNode } from "react"
import type { Season } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { useLatched, usePresence } from "@/shared/motion"
import { Segmented, Select } from "@/shared/ui"
import styles from "./map-explorer.module.css"
import {
  dependsOnSeason,
  METRIC_ICON,
  METRICS,
  type MetricKey,
  normativeId,
  SEASONS,
} from "./metric"

export interface MapToolbarProps {
  readonly children?: ReactNode
  readonly regionId?: string
  readonly regions?: readonly { readonly id: string; readonly name: string }[]
  readonly onRegion?: (id: string | null) => void
  readonly metric: MetricKey
  readonly season: Season
  readonly onMetric: (metric: MetricKey) => void
  readonly onSeason: (season: Season) => void
}

interface ToolbarSlotProps {
  readonly open: boolean
  readonly className?: string | undefined
  readonly children: ReactNode
}

function ToolbarSlot({ open, className, children }: ToolbarSlotProps) {
  const presence = usePresence(open)
  if (!presence.mounted) return null
  return (
    <div
      className={className ?? styles.slot}
      data-state={presence.state}
      inert={!open}
      onAnimationEnd={presence.onAnimationEnd}
    >
      {children}
    </div>
  )
}

export const MapToolbar = memo(function MapToolbar({
  metric,
  children,
  season,
  regionId = "",
  regions = [],
  onRegion,
  onMetric,
  onSeason,
}: MapToolbarProps) {
  const { t } = useTranslation()
  const seasonal = dependsOnSeason(metric)
  const seasonMetric = useLatched(metric, seasonal)
  return (
    <div className={styles.toolbar}>
      <Select
        label={t("data:metric.label")}
        hideLabel
        variant="floating"
        value={metric}
        onChange={onMetric}
        options={METRICS.map((key) => ({
          value: key,
          label: t(`data:metric.${key}`),
          icon: METRIC_ICON[key],
          group: t(normativeId(key) ? "normative:metricGroup" : "normative:baseGroup"),
        }))}
        className={styles.metric}
      />
      {normativeId(metric) && onRegion ? (
        <Select
          label={t("normative:regionSelect")}
          hideLabel
          variant="floating"
          value={regionId}
          onChange={(id) => onRegion(id || null)}
          options={[
            { value: "", label: t("normative:indexAllRegions") },
            ...regions.map((region) => ({ value: region.id, label: region.name })),
          ]}
        />
      ) : null}
      {children}
      <ToolbarSlot open={seasonal} className={styles.seasonSlot}>
        <Segmented
          label={t("data:season.legend")}
          value={season}
          onChange={onSeason}
          options={SEASONS.filter((key) => seasonMetric !== "hansen" || key !== "all").map(
            (key) => ({ value: key, label: t(`data:seasonShort.${key}`) }),
          )}
        />
      </ToolbarSlot>
    </div>
  )
})
