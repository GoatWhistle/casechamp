import type { Assessment } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { FactList } from "@/shared/ui"
import styles from "./normative-panel.module.css"

export function NormativePopulation({ result }: { readonly result: Assessment }) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (result.scenario.unknown_population_points > 0)
    return (
      <div>
        <p>
          {t(
            result.origin_basis === "fire_objects"
              ? "normative:fireObjectCount"
              : "normative:originCount",
            { count: f.integer(result.rows.length), value: f.integer(result.rows.length) },
          )}
        </p>
        <p>{t(populationExplanation(result))}</p>
        <ExcludedRows result={result} />
      </div>
    )
  return (
    <>
      <FactList
        label={t("normative:coverage")}
        items={[
          {
            key: "known",
            label: t("normative:populationKnown"),
            value: f.integer(result.scenario.within),
          },
          {
            key: "unknown",
            label: t("normative:populationUnknown"),
            value: f.integer(result.scenario.unknown),
          },
        ]}
      />
      <ExcludedRows result={result} />
    </>
  )
}

function populationExplanation(result: Assessment) {
  if (result.origin_basis === "fire_objects") return "normative:objectPopulationUnknown"
  if (result.criterion.mode === "walk") return "normative:populationNotKnown"
  return result.criterion.act === "132n"
    ? "normative:adultPopulationNotKnown"
    : "normative:missingPopulation"
}

function ExcludedRows({ result }: { readonly result: Assessment }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const unregulated = result.scenario.not_regulated_points ?? 0
  const inapplicable = result.scenario.not_applicable_points ?? 0
  if (unregulated + inapplicable === 0) return null
  const items = [
    { key: "unregulated", label: t("normative:unregulatedPoints"), count: unregulated },
    { key: "inapplicable", label: t("normative:inapplicablePoints"), count: inapplicable },
  ]
    .filter((item) => item.count > 0)
    .map(({ count, ...item }) => ({ ...item, value: f.integer(count) }))
  return (
    <div>
      <FactList label={t("normative:excludedPoints")} items={items} />
      <p className={styles.explanation}>{t("normative:excludedDenominator")}</p>
    </div>
  )
}
