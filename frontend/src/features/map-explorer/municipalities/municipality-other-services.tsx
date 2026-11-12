import { type MessageKey, useTranslation } from "@/shared/i18n"
import styles from "./municipality-index-card.module.css"
import {
  MunicipalityServiceValue,
  MunicipalityThreshold,
  type MunicipalNormative,
  serviceCoverage,
} from "./municipality-service-values"

const LABELS: Readonly<Record<string, MessageKey>> = {
  N03: "data:metric.normative_N03",
  N05: "data:metric.normative_N05",
  N06: "data:metric.normative_N06",
  N07: "data:metric.normative_N07",
  N08: "data:metric.normative_N08",
  N09: "data:metric.normative_N09",
}

export function MunicipalityOtherServices({
  rows,
}: {
  readonly rows: readonly MunicipalNormative[]
}) {
  const { t } = useTranslation()
  const available = rows.filter((row) => row.status === "available" && LABELS[row.criterion_id])
  if (!available.length) return null
  return (
    <section className={styles.rows} aria-label={t("map:municipalCard.otherServices")}>
      <p className={styles.headingRow}>{t("map:municipalCard.otherServices")}</p>
      {available.map((row) => (
        <div key={row.criterion_id}>
          <div className={styles.row}>
            <span>{t(LABELS[row.criterion_id] ?? "map:municipalCard.otherServices")}</span>
            <strong>
              <MunicipalityServiceValue row={row} />
            </strong>
          </div>
          <p className={styles.note}>
            <MunicipalityThreshold row={row} />
            <span>
              {t(
                serviceCoverage(row).population
                  ? "map:municipalCard.settlementEstimate"
                  : "map:municipalCard.pointShare",
              )}
            </span>
            {row.criterion_id === "N03" ? (
              <span>{t("map:municipalCard.fireAssumption")}</span>
            ) : null}
          </p>
        </div>
      ))}
    </section>
  )
}
