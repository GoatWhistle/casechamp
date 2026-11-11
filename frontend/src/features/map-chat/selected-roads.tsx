import type { RoadSegment } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { CloseButton, Icon } from "@/shared/ui"
import styles from "./map-chat.module.css"

export interface SelectedRoadsProps {
  readonly roads: readonly RoadSegment[]
  readonly onClear: () => void
}

export function SelectedRoads({ roads, onClear }: SelectedRoadsProps) {
  const { t } = useTranslation()
  const name = roads.length === 1 ? roads[0]?.name : ""
  if (!roads.length) return null
  return (
    <span className={styles.contextItem}>
      <Icon name="route" size="sm" />
      <span className={styles.contextText}>
        {name || t("chat:roads.count", { count: roads.length })}
      </span>
      <CloseButton label={t("chat:roads.clear")} onClick={onClear} />
    </span>
  )
}
