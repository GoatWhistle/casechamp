import { useFormatters, useTranslation } from "@/shared/i18n"
import { Skeleton, Stat } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"
import {
  MunicipalityServiceValue,
  MunicipalityThreshold,
  type MunicipalNormative as Normative,
  serviceCoverage,
} from "./municipality-service-values"

function MedicalValue({ row }: { readonly row: Normative | undefined }) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!row?.thresholds.length)
    return (
      <div className={styles.rows}>
        {String(row?.status) === "pending" ? (
          <>
            <Skeleton lines={2} />
            <p className={styles.note}>{t("map:municipalCard.pending")}</p>
          </>
        ) : (
          <p className={styles.note}>{t("map:municipalCard.unavailable")}</p>
        )}
      </div>
    )
  return (
    <div>
      <Stat
        label={t("map:municipalCard.within", {
          value: f.number(row.thresholds[0] ?? 0, 0),
          unit: t("map:municipalCard.minutes"),
        })}
        value={<MunicipalityServiceValue row={row} />}
      />
      {row.status === "available" ? (
        <p className={styles.note}>
          {t(
            serviceCoverage(row).population
              ? "map:municipalCard.settlementEstimate"
              : "map:municipalCard.pointShare",
          )}
        </p>
      ) : null}
    </div>
  )
}

export function MunicipalityServices({ rows }: { readonly rows: readonly Normative[] }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const school = rows.find((row) => row.criterion_id === "N04")
  const medical = ["N01", "N02"].map((id) => rows.find((row) => row.criterion_id === id))
  const schoolBasis = serviceCoverage(school).population
    ? "map:municipalCard.settlementEstimate"
    : "map:municipalCard.pointShare"

  return (
    <div className={styles.services}>
      <p className={styles.note}>{t("map:municipalCard.referenceEstimate")}</p>
      <section className={styles.rows} aria-label={t("map:municipalCard.school")}>
        <Stat
          label={t("map:municipalCard.school")}
          value={<MunicipalityServiceValue row={school} />}
        />
        <p className={styles.note}>
          <MunicipalityThreshold row={school} />
          {school?.status === "available" ? <span>{t(schoolBasis)}</span> : null}
        </p>
        {school?.mean_travel != null && school.unit === "metres" ? (
          <p className={styles.note}>
            {t("map:municipalCard.meanWalk", { value: f.number(school.mean_travel, 0) })}
          </p>
        ) : null}
      </section>
      <section className={styles.rows} aria-label={t("map:municipalCard.medical")}>
        <p className={styles.headingRow}>{t("map:municipalCard.medical")}</p>
        <div className={styles.medicalValues}>
          {medical.map((row, index) => (
            <MedicalValue key={row?.criterion_id ?? index} row={row} />
          ))}
        </div>
      </section>
    </div>
  )
}
