import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, DataTable, type DataTableColumn, NoValue } from "@/shared/ui"
import type { ComparisonData, ComparisonRow } from "../accessibility.queries"

export interface ComparisonTablesProps {
  readonly data: ComparisonData
}

export function ComparisonTables({ data }: ComparisonTablesProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const season: DataTableColumn<ComparisonRow> = {
    key: "season",
    header: t("accessibility:season"),
    cell: (row) => t(row.season === "summer" ? "accessibility:summer" : "accessibility:winter"),
  }
  const comparison: DataTableColumn<ComparisonRow>[] = [
    season,
    {
      key: "previous",
      header: t("accessibility:previous"),
      numeric: true,
      cell: (row) => f.number(row.previous, 2),
    },
    {
      key: "potential",
      header: t("accessibility:potential"),
      numeric: true,
      cell: (row) => f.number(row.potential, 2),
    },
    {
      key: "delta",
      header: t("accessibility:delta"),
      numeric: true,
      cell: (row) => f.number(row.delta, 2),
    },
    {
      key: "scheduled",
      header: t("accessibility:scheduled"),
      numeric: true,
      cell: (row) => (row.scheduled_index == null ? <NoValue /> : f.number(row.scheduled_index, 2)),
    },
  ]
  const effects: DataTableColumn<ComparisonRow>[] = [
    season,
    {
      key: "air",
      header: t("accessibility:air"),
      numeric: true,
      cell: (row) => f.number(row.potential - row.without_air, 2),
    },
    {
      key: "rail",
      header: t("accessibility:rail"),
      numeric: true,
      cell: (row) => f.number(row.potential - row.without_rail, 2),
    },
    {
      key: "water",
      header: t("accessibility:water"),
      numeric: true,
      cell: (row) => f.number(row.potential - row.without_water, 2),
    },
  ]
  const frequencyColumns: DataTableColumn<ComparisonRow>[] = [
    season,
    ...(["air", "rail", "water"] as const).map((mode) => ({
      key: mode,
      header: t(`accessibility:frequencyMode.${mode}`),
      numeric: true,
      cell: (row: ComparisonRow) => {
        const records = data.frequencies.filter(
          (item) =>
            item.season === row.season &&
            (mode === "water"
              ? item.mode === "ferry" || item.mode === "river"
              : item.mode === mode),
        )
        return t("accessibility:known", {
          known: records.reduce((sum, item) => sum + item.known, 0),
          total: records.reduce((sum, item) => sum + item.total, 0),
        })
      },
    })),
  ]
  return (
    <>
      <DataTable
        caption={t("accessibility:comparison")}
        columns={comparison}
        rows={data.rows}
        rowKey={(row) => row.season}
      />
      <Banner tone="info" title={t("accessibility:scheduleMissing")} />
      <p>{t("accessibility:effects")}</p>
      <DataTable
        caption={t("accessibility:effects")}
        columns={effects}
        rows={data.rows}
        rowKey={(row) => row.season}
      />
      <p>{t("accessibility:effectsHint")}</p>
      <p>{t("accessibility:frequency")}</p>
      <DataTable
        caption={t("accessibility:frequency")}
        columns={frequencyColumns}
        rows={data.rows}
        rowKey={(row) => row.season}
      />
      <p>{t("accessibility:frequencyHint")}</p>
    </>
  )
}
