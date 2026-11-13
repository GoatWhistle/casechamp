import type { ChatChart, ChatRow, ChatTable as Table } from "@/shared/api/chat-artifacts"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { BarChart, DataTable } from "@/shared/ui"
import { columnKey, displayCell, formatCell } from "./artifacts/table-format"
import styles from "./chat-artifacts.module.css"

export interface ChatArtifactsProps {
  readonly tables: readonly Table[]
  readonly charts: readonly ChatChart[]
}

export function ChatArtifacts({ tables, charts }: ChatArtifactsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const visibleTables = tables.filter(
    (table) =>
      charts.some((chart) => chart.table_id === table.id) ||
      (table.title !== "connectivity" && table.title !== "connectivity_summary"),
  )
  if (!visibleTables.length) return null
  return (
    <div className={styles.blocks}>
      {visibleTables.map((table) => {
        const chart = charts.find((item) => item.table_id === table.id)
        const y = table.columns.find((column) => column.key === chart?.y)
        const title = chart && y ? t(columnKey(y.key)) : t(`chat:tables.${table.title}`)
        return (
          <div key={table.id} className={styles.block}>
            <div className={styles.heading}>
              <strong>{title}</strong>
              {table.caption ? <span>{table.caption}</span> : null}
            </div>
            {chart && y ? (
              <BarChart
                label={title}
                items={table.rows.map((row) => {
                  const value = row[chart.y]
                  return {
                    key: String(row.id),
                    label: String(row[chart.x] ?? ""),
                    value: typeof value === "number" ? value : null,
                    display: value == null ? t("chat:missing") : formatCell(y, value, f),
                  }
                })}
              />
            ) : (
              <DataTable<ChatRow>
                scrollOrientation="horizontal"
                caption={table.caption ? `${title}: ${table.caption}` : title}
                className={styles.evidence}
                columns={table.columns.map((column) => ({
                  key: column.key,
                  header: t(
                    table.title === "scenario_indices" && column.key === "delta"
                      ? "chat:columns.changePoints"
                      : columnKey(column.key),
                  ),
                  numeric: column.format !== "text",
                  cell: (row) => (
                    <span className={column.format === "text" ? styles.name : undefined}>
                      {column.key === "after_minutes" && row.status_after === "unreachable"
                        ? t("chat:routeStatus.unreachable")
                        : displayCell(column, row[column.key], f, t)}
                    </span>
                  ),
                }))}
                rows={table.rows}
                rowKey={(row) => String(row.id)}
              />
            )}
            {table.truncated ? (
              <p className={styles.note}>
                {t("chat:tableRowsShown", { count: table.rows.length, total: table.total })}
              </p>
            ) : null}
            {!table.source.startsWith("model:") ? (
              <a className={styles.source} href={table.source} target="_blank" rel="noreferrer">
                {t("chat:tableSource")}
              </a>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
