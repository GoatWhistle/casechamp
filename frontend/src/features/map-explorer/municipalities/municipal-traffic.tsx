import { useMunicipalTraffic } from "@/entities/region"
import { isTrafficJob } from "@/shared/api/traffic"
import { showTrafficView } from "@/shared/hooks/use-traffic-view"
import { useTranslation } from "@/shared/i18n"
import { Button, HelpTip, Icon, Skeleton } from "@/shared/ui"
import styles from "./municipal-traffic.module.css"

export function MunicipalTraffic({
  regionId,
  municipalityId,
}: {
  readonly regionId: string
  readonly municipalityId: string
}) {
  const query = useMunicipalTraffic(regionId, municipalityId)
  const { t } = useTranslation()
  return (
    <section className={styles.content} aria-label={t("map:municipalTraffic.title")}>
      <p className={styles.heading}>
        <Icon name="route" />
        <strong>{t("map:municipalTraffic.title")}</strong>
        <HelpTip
          content={t("map:municipalTraffic.assumption")}
          label={t("map:municipalCard.metricHelp", { name: t("map:municipalTraffic.title") })}
        />
      </p>
      {query.isPending ? (
        <Skeleton lines={3} />
      ) : query.isError ? (
        <>
          <p>{t("map:municipalTraffic.unavailable")}</p>
          <Button variant="ghost" onClick={() => void query.refetch()}>
            {t("map:municipalTraffic.retry")}
          </Button>
        </>
      ) : (
        <>
          <Button
            variant="secondary"
            onClick={() => {
              if (isTrafficJob(query.data.view))
                showTrafficView(query.data.view, "baseline", "before")
            }}
          >
            {t("map:municipalTraffic.showLoad")}
          </Button>
        </>
      )}
    </section>
  )
}
