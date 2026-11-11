import type { StressSummary as Summary } from "@/shared/api/road-stress"
import { useTranslation } from "@/shared/i18n"
import { Skeleton, Stat } from "@/shared/ui"
import styles from "./stress-summary.module.css"

export function StressSummary({ summary }: { readonly summary: Summary | undefined }) {
  const { t } = useTranslation()
  const totals = summary?.totals
  if (!totals) return <Skeleton />
  return (
    <div className={styles.summary} data-stress-summary={summary.region || "national"}>
      <Stat
        className={styles.metric}
        label={t("stress:lostAccess")}
        value={t("stress:pointCount", { count: totals.isolated_points })}
      />
      <Stat
        className={styles.metric}
        label={t("stress:isolatedResidents")}
        value={t("stress:populationCount", { count: totals.isolated_population })}
      />
      <Stat
        className={styles.metric}
        label={t("stress:maxDelay")}
        value={t("stress:minuteCount", { minutes: Math.round(totals.max_delay_minutes) })}
      />
      <Stat
        className={styles.metric}
        label={t("stress:exposedResidents")}
        value={t("stress:populationCount", { count: totals.exposed_population })}
      />
      <p className={styles.note}>
        {t("stress:summary", {
          regions: totals.affected_regions,
          points: totals.affected_points,
        })}
      </p>
      <p className={styles.note}>{t("stress:summaryLimit")}</p>
    </div>
  )
}
