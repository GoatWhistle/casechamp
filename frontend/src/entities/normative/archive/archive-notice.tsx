import { useFormatters, useTranslation } from "@/shared/i18n"
import { Disclosure, StatusBadge } from "@/shared/ui"
import type { IndexMapRegion } from "../indices"
import styles from "./archive-notice.module.css"

export function ArchiveNotice({
  row,
  compact = false,
}: {
  readonly row: IndexMapRegion
  readonly compact?: boolean
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (row.data_source !== "archived_aggregate") return null
  return (
    <div className={styles.notice}>
      <StatusBadge tone="warning" label={t("normative:archive.label")} />
      {!compact ? <p>{t("normative:archive.note")}</p> : null}
      {row.measured_at ? (
        <p>{t("normative:indexCalculatedAt", { date: f.date(row.measured_at) })}</p>
      ) : null}
      {!compact ? (
        <Disclosure title={t("normative:archive.source")}>
          {row.source_report ? <p>{row.source_report}</p> : null}
          {row.source_report_sha256 ? <p>{row.source_report_sha256}</p> : null}
          {row.source_checked_at ? (
            <p>{t("normative:archive.checked", { date: f.date(row.source_checked_at) })}</p>
          ) : null}
        </Disclosure>
      ) : null}
    </div>
  )
}
