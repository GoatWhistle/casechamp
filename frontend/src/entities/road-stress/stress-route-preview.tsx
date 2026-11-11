import type { StressRouteComparison } from "@/shared/api/road-stress"
import { showStressView } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./stress-card.module.css"

export function StressRoutePreview({
  jobId,
  route,
}: {
  readonly jobId: string
  readonly route: StressRouteComparison
}) {
  const { t } = useTranslation()
  return (
    <div>
      <p>
        {route.origin.name} / {route.destination.name}
      </p>
      <div className={styles.comparison}>
        {(["before", "after"] as const).map((key) => (
          <p key={key}>
            <strong>{t(`stress:${key}`)}</strong>{" "}
            {route[key].status === "reachable"
              ? t("stress:travel", {
                  minutes: Math.round((route[key].hours ?? 0) * 60),
                  km: Math.round(route[key].km ?? 0),
                })
              : t("stress:noPath")}
          </p>
        ))}
      </div>
      <Button
        icon="map"
        variant="secondary"
        onClick={() => showStressView({ jobId, impacts: [], route })}
      >
        {t("stress:compare")}
      </Button>
    </div>
  )
}
