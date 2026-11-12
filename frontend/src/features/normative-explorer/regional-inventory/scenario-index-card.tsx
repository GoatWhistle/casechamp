import type { RegionalIndex } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Card, NoValue, Stat, StatusBadge } from "@/shared/ui"
import { PopulationReference } from "./index-details"
import styles from "./regional-index-card.module.css"

export function ScenarioIndexCard({
  index,
  stage,
}: {
  readonly index: NonNullable<RegionalIndex["model_index"]>
  readonly stage: NormativeRouteStage
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const values = stage === "baseline" ? index.baseline : index.scenario
  return (
    <Card as="div" title={t("normative:scenarioIndexTitle")} className={styles.index}>
      <StatusBadge tone="warning" label={t("normative:indexStatuses.scenarioReady")} />
      <p>{t("normative:scenarioIndexNote")}</p>
      <p>{t("normative:indexCalculatedAt", { date: f.date(index.measured_at) })}</p>
      {index.policy.fire_speed_kmh !== null ? (
        <p>
          {t("normative:scenarioFireSpeed", { speed: f.number(index.policy.fire_speed_kmh, 0) })}
        </p>
      ) : (
        <p>
          {t(
            index.policy.mode === "walk"
              ? "normative:scenarioWalkMode"
              : "normative:scenarioCarMode",
          )}
        </p>
      )}
      {values.map((value) => {
        const score =
          index.policy.weighting === "population"
            ? value.population_share_percent
            : value.point_share_percent
        return (
          <div key={value.threshold} className={styles.value}>
            <Stat
              label={t(
                index.policy.unit === "metres"
                  ? "normative:scenarioMetreLimit"
                  : "normative:scenarioMinuteLimit",
                { value: f.number(value.threshold, 0) },
              )}
              value={score === null ? <NoValue /> : f.number(score, 1)}
              unit={t("normative:indexPercentUnit")}
            />
            <p>
              {t(
                index.policy.weighting === "population"
                  ? "normative:indexPopulationBasis"
                  : "normative:indexPointBasis",
              )}
            </p>
            {index.policy.weighting === "population" ? <PopulationReference value={value} /> : null}
            <p>
              {t("normative:indexReferenceCount", {
                within: f.integer(value.within_points),
                total: f.integer(value.reference_points),
                unresolved: f.integer(value.unresolved_points),
              })}
            </p>
          </div>
        )
      })}
    </Card>
  )
}
