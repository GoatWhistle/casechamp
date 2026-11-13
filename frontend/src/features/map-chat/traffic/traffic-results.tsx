import type { TrafficJob, TrafficMode } from "@/shared/api/traffic"
import { showTrafficView, useTrafficView } from "@/shared/hooks/use-traffic-view"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Disclosure, Segmented, Stat } from "@/shared/ui"
import { TrafficIndex } from "./traffic-index"
import styles from "./traffic-results.module.css"

export function TrafficResults({ job }: { readonly job: TrafficJob }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const view = useTrafficView()
  const active = view.job?.id === job.id
  const variant = active ? view.variant : "baseline"
  return (
    <div className={styles.results}>
      {job.id.startsWith("municipal-baseline-") ? (
        <Button variant="secondary" onClick={() => showTrafficView(job, "baseline", "before")}>
          {t("map:municipalTraffic.showLoad")}
        </Button>
      ) : (
        <TrafficIndex job={job} variant={variant} />
      )}
      <Disclosure title={t("traffic:loadDetails")}>
        <Segmented<TrafficMode>
          label={t("traffic:mapMode")}
          options={[
            { value: "project", label: t("traffic:mode.project") },
            { value: "before", label: t("traffic:mode.before") },
            { value: "after", label: t("traffic:mode.after") },
            { value: "difference", label: t("traffic:mode.difference") },
          ]}
          value={active ? view.mode : "project"}
          onChange={(mode) => showTrafficView(job, variant, mode)}
        />
        {active && view.selected ? (
          <div className={styles.stats}>
            <Stat label={t("traffic:flowBefore")} value={f.number(view.selected.flow_before, 0)} />
            <Stat label={t("traffic:flowAfter")} value={f.number(view.selected.flow_after, 0)} />
          </div>
        ) : null}
      </Disclosure>
    </div>
  )
}
