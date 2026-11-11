import { useState } from "react"
import type { RoadJob } from "@/shared/api/road-graph"
import type { components } from "@/shared/api/schema.gen"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, DataTable, Disclosure, NoValue, Select } from "@/shared/ui"
import { AppraisalAssumptions } from "./appraisal-assumptions"

const metrics = [
  "annual_passenger_hours",
  "annual_passenger_rub",
  "annual_vehicle_hours",
  "annual_vehicle_km",
  "annual_freight_rub",
  "annual_gross_rub",
  "annual_net_rub",
  "present_benefits_rub",
  "present_costs_rub",
  "net_present_value_rub",
  "benefit_cost_ratio",
  "discounted_payback_year",
] as const

type Scenario = components["schemas"]["AppraisalScenario"]

export function AppraisalResult({ job }: { readonly job: RoadJob }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [selected, setSelected] = useState<"low" | "base" | "high">("base")
  const result = job.appraisal_result
  const assumptions = job.appraisal_assumptions
  if (!result || !assumptions) return null
  const values = (name: string, metric: (typeof metrics)[number]) => {
    const scenario: Scenario | undefined = result.scenarios.find((s) => s.name === name)
    const value = scenario?.[metric]
    return value == null ? <NoValue /> : f.number(value, 2)
  }
  return (
    <>
      <p>{t("appraisal:title")}</p>
      <p>{t("appraisal:resultHint")}</p>
      {result.unresolved_passenger_flows ? (
        <Banner
          tone="warning"
          title={t("appraisal:missingTravel", { count: result.unresolved_passenger_flows })}
        />
      ) : null}
      {result.unresolved_freight_flows ? (
        <Banner
          tone="warning"
          title={t("appraisal:missingFreight", { count: result.unresolved_freight_flows })}
        />
      ) : null}
      {result.freight_routing_scope === "road_network_vehicle_constraints_unverified" ? (
        <p>{t("appraisal:freightConstraints")}</p>
      ) : null}
      <Select
        label={t("appraisal:resultScenario")}
        value={selected}
        onChange={setSelected}
        options={(["low", "base", "high"] as const).map((value) => ({
          value,
          label: t(`appraisal:scenarioNames.${value}`),
        }))}
      />
      <DataTable
        caption={t("appraisal:summaryTable")}
        rows={[...metrics]}
        rowKey={(m) => m}
        columns={[
          {
            key: "metric",
            header: t("appraisal:metric"),
            cell: (m) => t(`appraisal:metrics.${m}`),
          },
          {
            key: selected,
            header: t(`appraisal:scenarioNames.${selected}`),
            numeric: true,
            cell: (m) => values(selected, m),
          },
        ]}
      />
      <p>{t("appraisal:noPayback")}</p>
      {result.travel.length ? (
        <Disclosure title={t("appraisal:travelTable")}>
          <DataTable
            caption={t("appraisal:travelTable")}
            rows={result.travel}
            rowKey={(row) => `${row.origin_point_id}/${row.market_city}`}
            columns={[
              {
                key: "direction",
                header: t("appraisal:direction"),
                cell: (row) => {
                  const flow = assumptions.passengers.find(
                    (p) =>
                      p.origin_point_id === row.origin_point_id &&
                      p.market_city === row.market_city,
                  )
                  return `${flow?.origin_name || row.origin_point_id} / ${row.market_city}`
                },
              },
              {
                key: "before",
                header: t("appraisal:beforeHours"),
                numeric: true,
                cell: (row) =>
                  row.before_hours == null ? <NoValue /> : f.number(row.before_hours, 2),
              },
              {
                key: "after",
                header: t("appraisal:afterHours"),
                numeric: true,
                cell: (row) =>
                  row.after_hours == null ? <NoValue /> : f.number(row.after_hours, 2),
              },
            ]}
          />
        </Disclosure>
      ) : null}
      <AppraisalAssumptions value={assumptions} />
    </>
  )
}
