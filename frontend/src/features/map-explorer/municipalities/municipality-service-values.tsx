import type { components } from "@/shared/api"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { NoValue } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"

export type MunicipalNormative =
  components["schemas"]["MunicipalityIndicesResponse"]["normative"][number]

export function serviceCoverage(row: MunicipalNormative | undefined) {
  const values = row?.values ?? []
  const population =
    values.length > 0 && values.every((value) => value.population_share_percent !== null)
  const shares = values.flatMap((value) => {
    const share = population ? value.population_share_percent : value.point_share_percent
    return share !== null && Number.isFinite(share) ? [share] : []
  })
  return {
    population,
    min: shares.length ? Math.min(...shares) : null,
    max: shares.length ? Math.max(...shares) : null,
  }
}

export function MunicipalityServiceValue({
  row,
}: {
  readonly row: MunicipalNormative | undefined
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (String(row?.status) === "pending")
    return <span className={styles.note}>{t("map:municipalCard.pending")}</span>
  const { min, max } = serviceCoverage(row)
  if (row?.status !== "available" || min === null || max === null)
    return <NoValue label={t("map:municipalCard.unavailable")} />
  return min === max
    ? f.percent(min / 100, 0)
    : t("map:municipalCard.range", { min: f.number(min, 0), max: f.number(max, 0) })
}

export function MunicipalityThreshold({ row }: { readonly row: MunicipalNormative | undefined }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const values = row?.thresholds ?? []
  if (!values.length) return null
  const min = Math.min(...values),
    max = Math.max(...values)
  const limit =
    min === max
      ? f.number(min, 0)
      : t("map:municipalCard.limitRange", { min: f.number(min, 0), max: f.number(max, 0) })
  const unit = t(row?.unit === "metres" ? "map:municipalCard.metres" : "map:municipalCard.minutes")
  return <span>{t("map:municipalCard.within", { value: limit, unit })}</span>
}
