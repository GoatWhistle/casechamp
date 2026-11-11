import { useFormatters, useTranslation } from "@/shared/i18n"
import { Disclosure } from "@/shared/ui"
import type { Project } from "./appraisal-state"

export function AppraisalAssumptions({ value }: { readonly value: Project }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <Disclosure title={t("appraisal:assumptions")}>
      <p>
        {t("appraisal:projectSummary", {
          year: value.price_year,
          horizon: value.horizon_years,
          rate: f.number(value.discount_rate * 100, 2),
          capital: value.capital_cost_rub,
          operating: value.annual_operating_cost_rub,
        })}
      </p>
      <p>{value.cost_source}</p>
      {value.scenarios.map((s) => (
        <p key={s.name}>
          {t("appraisal:scenarioSummary", {
            name: t(`appraisal:scenarioNames.${s.name}`),
            demand: f.number(s.demand_factor, 2),
            value: f.number(s.value_factor, 2),
          })}
        </p>
      ))}
      {value.passengers.map((p) => (
        <p key={`${p.origin_point_id}/${p.market_city}`}>
          {t("appraisal:flowSummary", {
            origin: p.origin_name || p.origin_point_id,
            target: p.market_city,
            trips: p.trips_per_year,
            rate: p.rub_per_hour,
            basis: t(p.basis === "observed" ? "appraisal:observed" : "appraisal:assumed"),
            source: p.source,
          })}
        </p>
      ))}
      {(value.freight ?? []).map((p) => (
        <p key={p.name}>
          {p.origin_point_id && p.market_city
            ? t("appraisal:freightRoutedSummary", {
                name: p.name,
                origin: p.origin_point_id,
                target: p.market_city,
                source: p.source,
              })
            : t("appraisal:freightSummary", {
                name: p.name,
                trips: p.trips_per_year,
                beforeHours: f.number(p.before_hours ?? Number.NaN, 2),
                afterHours: f.number(p.after_hours ?? Number.NaN, 2),
                beforeKm: f.number(p.before_km ?? Number.NaN, 2),
                afterKm: f.number(p.after_km ?? Number.NaN, 2),
                hourRate: p.rub_per_vehicle_hour,
                kmRate: p.rub_per_km,
                basis: t(p.basis === "observed" ? "appraisal:observed" : "appraisal:assumed"),
                source: p.source,
              })}
        </p>
      ))}
    </Disclosure>
  )
}
