import { useId } from "react"
import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Disclosure, HelpTip, Stat } from "@/shared/ui"
import { AppraisalResult } from "./appraisal/appraisal-result"
import styles from "./road-scenario.module.css"

export function RoadMoney({ job }: { readonly job: RoadJob }) {
  const { t } = useTranslation()
  const titleId = useId()
  if (job.appraisal_result) return <AppraisalResult job={job} />
  const money = job.result?.money
  return (
    <section className={styles.section} aria-labelledby={titleId}>
      <div className={styles.sectionHead}>
        <p id={titleId} className={styles.sectionTitle}>
          {t("graph:money.title")}
        </p>
        <HelpTip content={t("graph:moneyMethod")} label={t("common:ui.hint")} />
      </div>
      {money ? (
        <>
          <div className={styles.pair}>
            <Stat
              label={t("graph:moneyGross")}
              value={t("graph:rubles", { value: money.annual_gross_rub })}
            />
            <Stat
              label={t("graph:moneyNet")}
              value={t("graph:rubles", { value: money.annual_net_rub })}
            />
            {money.simple_payback_years !== null && money.simple_payback_years !== undefined ? (
              <Stat
                label={t("graph:payback")}
                value={t("graph:years", { value: money.simple_payback_years })}
              />
            ) : null}
          </div>
          <Disclosure title={t("graph:money.assumptions")}>
            <p className={styles.hint}>
              {t("graph:moneyFlow", {
                origin: money.assumptions.origin_point_id,
                target: money.assumptions.market_city,
                trips: money.assumptions.trips_per_year,
                rate: money.assumptions.rub_per_hour,
                hours: money.hours_saved_per_trip,
              })}
            </p>
            <p className={styles.hint}>
              {t("graph:moneyCosts", {
                capital: money.assumptions.capital_cost_rub,
                operating: money.assumptions.annual_operating_cost_rub,
              })}
            </p>
          </Disclosure>
        </>
      ) : (
        <p className={styles.hint}>
          {t(job.money_assumptions ? "graph:moneyUnavailable" : "graph:moneyPrompt")}
        </p>
      )}
    </section>
  )
}
