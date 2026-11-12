import type { Assessment, Criterion } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { NoValue, Stat } from "@/shared/ui"
import styles from "./normative-panel.module.css"

export function NormativeCoverage({ result }: { readonly result: Assessment | null | undefined }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const lower = result?.scenario.lower_percent
  const upper = result?.scenario.upper_percent
  const description =
    result?.origin_basis === "fire_objects"
      ? "normative:fireObjectCoverageNote"
      : coverageDescription(result?.criterion)
  const excluded =
    (result?.scenario.not_regulated_points ?? 0) + (result?.scenario.not_applicable_points ?? 0)
  const noNumericScope = excluded > 0 && excluded === result?.rows.length
  const noNumericResult = coverageUndetermined(result)
  const measured = measuredPaths(result)
  return (
    <>
      {result ? (
        <>
          <p>{t("normative:pilotCoverage", { region: result.region })}</p>
          <Stat
            label={t("normative:measuredPaths")}
            value={t("normative:measuredPathCount", {
              known: f.integer(measured),
              total: f.integer(result.rows.length),
            })}
          />
        </>
      ) : null}
      <Stat
        label={t(coverageTitle(result, noNumericResult))}
        value={
          noNumericScope ? (
            t("normative:numericCoverageUnavailable")
          ) : noNumericResult ? (
            t("normative:coverageUndetermined")
          ) : lower == null || upper == null ? (
            <NoValue />
          ) : (
            t("normative:boundsShort", { lower: f.number(lower, 1), upper: f.number(upper, 1) })
          )
        }
      />
      {result ? (
        <p className={styles.explanation}>
          {t(noNumericScope ? "normative:numericCoverageExplanation" : description)}
        </p>
      ) : null}
    </>
  )
}

function coverageDescription(criterion: Criterion | undefined) {
  if (criterion?.service === "fire") return "normative:fireCoverageNote"
  if (criterion?.service === "library") return "normative:libraryExplanation"
  if (criterion?.act === "132n") return "normative:medicalScope"
  if (criterion?.mode !== "walk") return "normative:unknownLimit"
  return criterion.service === "stop"
    ? "normative:walkingStopExplanation"
    : "normative:walkingExplanation"
}

function coverageUndetermined(result: Assessment | null | undefined) {
  if (!result) return false
  if (result.scenario.lower_percent == null || result.scenario.upper_percent == null) return true
  return result.scenario.population > 0 && result.scenario.unknown === result.scenario.population
}

function coverageTitle(result: Assessment | null | undefined, undetermined: boolean) {
  if (result?.origin_basis === "fire_objects") return "normative:objectCoverage"
  return undetermined ? "normative:qualificationCoverage" : "normative:coverage"
}

function measuredPaths(result: Assessment | null | undefined) {
  return (
    result?.rows.filter((row) => row.minutes != null || row.distance_metres != null).length ?? 0
  )
}
