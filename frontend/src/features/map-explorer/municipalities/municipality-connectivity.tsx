import type { components } from "@/shared/api"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { HelpTip, NoValue, Stat } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"

export function MunicipalityConnectivity({
  data,
}: {
  readonly data: components["schemas"]["MunicipalityIndicesResponse"]
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const explanation = [
    data.region_connectivity.status === "available" && data.region_connectivity.value !== null
      ? t("map:municipalCard.regionComparison", {
          value: f.number(data.region_connectivity.value, 1),
        })
      : t("map:municipalCard.unavailable"),
    data.connectivity.population_coverage !== null
      ? t("map:municipalCard.coverage", {
          value: f.percent(data.connectivity.population_coverage, 0),
        })
      : null,
  ]
    .filter(Boolean)
    .join(". ")
  return (
    <div className={styles.rows}>
      <Stat
        layout="row"
        icon="link"
        label={t("map:municipalCard.hansen")}
        help={
          <HelpTip
            content={explanation}
            label={t("map:municipalCard.metricHelp", { name: t("map:municipalCard.hansen") })}
          />
        }
        value={
          data.connectivity.status === "available" && data.connectivity.value !== null ? (
            f.number(data.connectivity.value, 1)
          ) : (
            <NoValue />
          )
        }
      />
    </div>
  )
}
