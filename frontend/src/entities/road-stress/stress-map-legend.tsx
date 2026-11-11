import { showStressView, useStressView } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button, Card, Icon } from "@/shared/ui"
import styles from "./stress-map-legend.module.css"

export function StressMapLegend() {
  const view = useStressView()
  const { t } = useTranslation()
  if (!view.jobId) return null
  return (
    <Card as="aside" className={styles.legend} title={t("stress:title")}>
      <p className={styles.closed}>
        <Icon name="route" />
        {t("stress:closedLegend")}
      </p>
      {view.route?.after.coordinates.length ? (
        <p className={styles.detour}>
          <Icon name="route" />
          {t("stress:detourLegend")}
        </p>
      ) : null}
      {view.route ? <p>{t("stress:baseLegend")}</p> : <p>{t("stress:routeNotSelected")}</p>}
      {view.showPoints !== false ? <p>{t("stress:pointsLegend")}</p> : null}
      <Button
        icon="x"
        variant="ghost"
        onClick={() => showStressView({ jobId: null, impacts: [], route: null })}
      >
        {t("stress:hideMap")}
      </Button>
    </Card>
  )
}
