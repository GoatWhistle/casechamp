import type { RoadGraphState } from "@/entities/road-graph"
import { useTranslation } from "@/shared/i18n"
import { usePresence } from "@/shared/motion"
import { Button, Switch } from "@/shared/ui"
import styles from "./map-legend.module.css"

export interface RoadLegendProps {
  readonly roads: RoadGraphState
}

export function RoadLayer({ roads }: RoadLegendProps) {
  const { t } = useTranslation()
  return (
    <div className={styles.row}>
      <Switch label={t("graph:layer")} checked={roads.enabled} onChange={roads.setEnabled} />
    </div>
  )
}

export function OverlayReset({ roads }: RoadLegendProps) {
  const { t } = useTranslation()
  const overlay = usePresence(roads.hasOverlay)
  if (!overlay.mounted) return null
  return (
    <div
      className={styles.reveal}
      data-state={overlay.state}
      onAnimationEnd={overlay.onAnimationEnd}
    >
      <Button variant="ghost" size="compact" icon="minus" onClick={roads.clearOverlays}>
        {t("graph:clearMap")}
      </Button>
    </div>
  )
}
