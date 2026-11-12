import { useState } from "react"
import { type AccessRow, type Assessment, NormativeMap } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, Card, DataTable, NoValue, Select } from "@/shared/ui"
import styles from "./normative-explorer.module.css"

export function NormativeResults({ result }: { readonly result: Assessment }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [filter, setFilter] = useState("all")
  const keys = ["within", "exceeded", "unreachable", "unknown"] as const
  const rows = result.rows.filter((row) => filter === "all" || row.state === filter)
  const summary = result.scenario
  return (
    <div className={styles.results}>
      <Card title={t("normative:mapTitle")} description={t("normative:mapLegend")}>
        <NormativeMap
          rows={result.rows}
          facilities={result.facilities}
          label={t("normative:mapTitle")}
          stateLabel={(state) => t(`normative:states.${state}`)}
        />
      </Card>
      <Card title={t("normative:coverage")}>
        <p className={styles.summary}>
          {summary.lower_percent === null || summary.upper_percent === null
            ? t("normative:missingPopulation")
            : t("normative:bounds", {
                lower: f.number(summary.lower_percent, 1),
                upper: f.number(summary.upper_percent, 1),
              })}
        </p>
        <p>{t("normative:known", { value: f.integer(summary.within) })}</p>
        <p>{t("normative:unknown", { value: f.integer(summary.unknown) })}</p>
        {result.coverage_loss_pp === null ? null : (
          <p>{t("normative:loss", { value: f.number(result.coverage_loss_pp, 1) })}</p>
        )}
        <p className={styles.note}>{t("normative:boundsExplanation")}</p>
      </Card>
      <Select
        label={t("normative:filter")}
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all", label: t("normative:all") },
          ...keys.map((value) => ({ value, label: t(`normative:states.${value}`) })),
        ]}
      />
      <DataTable<AccessRow>
        caption={t("normative:results")}
        rows={rows}
        rowKey={(row) => row.id}
        defaultSort={{ key: "population", direction: "descending" }}
        columns={[
          {
            key: "name",
            header: t("normative:settlement"),
            cell: (row) => row.name,
            sortValue: (row) => row.name,
          },
          {
            key: "population",
            header: t("normative:population"),
            numeric: true,
            cell: (row) => (row.population === null ? <NoValue /> : f.integer(row.population)),
            sortValue: (row) => row.population,
          },
          {
            key: "minutes",
            header: t("normative:minutes"),
            numeric: true,
            cell: (row) => (row.minutes === null ? <NoValue /> : f.number(row.minutes, 1)),
            sortValue: (row) => row.minutes,
          },
          {
            key: "state",
            header: t("normative:state"),
            cell: (row) => t(`normative:states.${row.state}`),
          },
        ]}
      />
      <Banner tone="neutral" title={t("normative:graph", { revision: result.graph_revision })} />
    </div>
  )
}
