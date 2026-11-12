import { clearTrafficView, useTrafficView } from "@/shared/hooks/use-traffic-view"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./traffic-key.module.css"

export function TrafficKey() {
  const { t } = useTranslation()
  const view = useTrafficView()
  if (view.job?.status !== "completed") return null
  const proposal = view.job.alternatives.find((row) => row.id === view.variant)
  const names = proposal?.road_names?.filter((name) => !/^\d{7,}$/.test(name)).join(", ")
  const project = view.mode === "project"
  if (
    project &&
    (!proposal || (proposal.kind === "connection" && proposal.housing_clearance !== true))
  )
    return null
  return (
    <div className={styles.key}>
      <strong>
        {names || (proposal ? t(`traffic:kind.${proposal.kind}`) : t("traffic:legend"))}
      </strong>
      {proposal ? <span>{t("traffic:projectLength", { value: proposal.length_km })}</span> : null}
      <ul className={styles.items}>
        {!project || proposal?.kind !== "connection" ? (
          <li>
            <span className={styles.road} aria-hidden="true" />
            {t(project ? "traffic:legendProject" : "traffic:legendRoad")}
          </li>
        ) : null}
        {proposal?.kind === "connection" && view.mode !== "before" ? (
          <li>
            <span className={styles.connection} aria-hidden="true" />
            {t("traffic:legendNew")}
          </li>
        ) : null}
        {view.mode === "difference" ? (
          <li>
            <span className={styles.relief} aria-hidden="true" />
            {t("traffic:legendRelief")}
          </li>
        ) : null}
      </ul>
      <p>{t(`traffic:mode.${view.mode}`)}</p>
      <Button icon="x" variant="ghost" size="compact" onClick={clearTrafficView}>
        {t("traffic:hide")}
      </Button>
    </div>
  )
}
