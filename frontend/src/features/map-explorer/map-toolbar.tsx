import { memo, type ReactNode } from "react"
import { useTranslation } from "@/shared/i18n"
import { Select } from "@/shared/ui"
import styles from "./map-explorer.module.css"
import { type MetricKey, normativeId } from "./metric"

export interface MapToolbarProps {
  readonly children?: ReactNode
  readonly regionId?: string
  readonly regions?: readonly { readonly id: string; readonly name: string }[]
  readonly onRegion?: (id: string | null) => void
  readonly metric: MetricKey
}

export const MapToolbar = memo(function MapToolbar({
  metric,
  children,
  regionId = "",
  regions = [],
  onRegion,
}: MapToolbarProps) {
  const { t } = useTranslation()
  return (
    <div className={styles.toolbar}>
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
    </div>
  )
})
