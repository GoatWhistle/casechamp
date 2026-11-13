import { useTranslation } from "@/shared/i18n"
import { HelpTip, Stat } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"
import {
  MunicipalityServiceHelp,
  MunicipalityServiceValue,
  type MunicipalNormative as Normative,
  useMunicipalityThreshold,
} from "./municipality-service-values"

export function MunicipalityServices({ rows }: { readonly rows: readonly Normative[] }) {
  const { t } = useTranslation()
  const school = rows.find((row) => row.criterion_id === "N04")
  const emergency = rows.find((row) => row.criterion_id === "N01")
  const urgent = rows.find((row) => row.criterion_id === "N02")
  const emergencyThreshold = useMunicipalityThreshold(emergency)
  const urgentThreshold = useMunicipalityThreshold(urgent)
  return (
    <div className={styles.services}>
      <section className={styles.metric} aria-label={t("map:municipalCard.school")}>
        <Stat
          layout="row"
          icon="school"
          label={t("map:municipalCard.school")}
          value={<MunicipalityServiceValue row={school} />}
          help={<MunicipalityServiceHelp row={school} label={t("map:municipalCard.school")} />}
        />
      </section>
      <section className={styles.metric} aria-label={t("map:municipalCard.medical")}>
        <Stat
          layout="row"
          icon="hospital"
          label={t("map:municipalCard.medical")}
          help={
            <HelpTip
              label={t("map:municipalCard.medicalHelp")}
              content={t("map:municipalCard.medicalOrder", {
                emergency: emergencyThreshold ?? t("map:municipalCard.unavailable"),
                urgent: urgentThreshold ?? t("map:municipalCard.unavailable"),
              })}
            />
          }
          value={
            <span className={styles.pair}>
              <MunicipalityServiceValue row={emergency} />
              <span>{t("map:municipalCard.pairSeparator")}</span>
              <MunicipalityServiceValue row={urgent} />
            </span>
          }
        />
      </section>
    </div>
  )
}
