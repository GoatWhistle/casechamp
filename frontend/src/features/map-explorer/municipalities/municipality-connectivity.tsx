import type { components } from "@/shared/api"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { NoValue } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"

export function MunicipalityConnectivity({
  data,
}: {
  readonly data: components["schemas"]["MunicipalityIndicesResponse"]
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <div className={styles.rows}>
      <div className={styles.row}>
        <span>{t("map:municipalCard.hansen")}</span>
        <strong>
          {data.connectivity.status === "available" && data.connectivity.value !== null ? (
            f.number(data.connectivity.value, 2)
          ) : (
            <NoValue />
          )}
        </strong>
      </div>
      {data.region_connectivity.status === "available" &&
      data.region_connectivity.value !== null ? (
        <p className={styles.note}>
          {t("map:municipalCard.regionComparison", {
            value: f.number(data.region_connectivity.value, 2),
          })}
        </p>
      ) : null}
      {data.connectivity.population_coverage !== null ? (
        <p className={styles.note}>
          {t("map:municipalCard.coverage", {
            value: f.percent(data.connectivity.population_coverage, 0),
          })}
        </p>
      ) : null}
    </div>
  )
}
