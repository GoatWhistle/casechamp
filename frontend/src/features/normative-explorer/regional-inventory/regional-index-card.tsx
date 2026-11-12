import { type RegionalIndex, useRegionalIndex } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { type MessageKey, useFormatters, useTranslation } from "@/shared/i18n"
import {
  ButtonLink,
  Card,
  Disclosure,
  EmptyState,
  ErrorState,
  NoValue,
  Skeleton,
  Stat,
  StatusBadge,
} from "@/shared/ui"
import { IndexReview, PopulationReference } from "./index-details"
import { IndexMeasurement } from "./index-measurement"
import styles from "./regional-index-card.module.css"
import { ScenarioIndexCard } from "./scenario-index-card"

export function RegionalIndexCard({
  regionId,
  criterionId,
  runId,
  stage,
}: {
  readonly regionId: string
  readonly criterionId: string
  readonly runId?: string | undefined
  readonly stage: NormativeRouteStage
}) {
  const index = useRegionalIndex(regionId, criterionId, runId)
  const { t } = useTranslation()
  if (index.isPending) return <Skeleton lines={4} />
  if (index.isError)
    return <ErrorState title={t("normative:loadError")} onRetry={() => void index.refetch()} />
  if (index.data.model_index && !index.data.scenario.length)
    return (
      <>
        <ScenarioIndexCard index={index.data.model_index} stage={stage} />
        {index.data.basis ? <IndexUnavailable index={index.data} /> : null}
      </>
    )
  if (!index.data.basis)
    return (
      <EmptyState
        icon="info"
        title={t("normative:indexBasisMissing")}
        description={t("normative:indexBasisMissingNote")}
      />
    )
  if (!index.data.scenario.length) return <IndexUnavailable index={index.data} />
  return <IndexValues index={index.data} stage={stage} />
}

function IndexValues({
  index,
  stage,
}: {
  readonly index: RegionalIndex
  readonly stage: NormativeRouteStage
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const basis = index.basis
  if (!basis) return null
  const values = stage === "baseline" ? index.baseline : index.scenario
  return (
    <Card as="div" title={t("normative:indexTitle")} className={styles.index}>
      <StatusBadge tone="warning" label={t("normative:indexConditional")} />
      {index.model_index?.policy.fire_speed_kmh != null ? (
        <p>
          {t("normative:scenarioFireSpeed", {
            speed: f.number(index.model_index.policy.fire_speed_kmh, 0),
          })}
        </p>
      ) : null}
      {index.measured_at ? (
        <p>{t("normative:indexCalculatedAt", { date: f.date(index.measured_at) })}</p>
      ) : null}
      {values.map((value) => {
        const score =
          index.weighting === "population"
            ? value.population_share_percent
            : value.point_share_percent
        return (
          <div key={value.threshold} className={styles.value}>
            <Stat
              label={t(
                basis.unit === "metres"
                  ? "normative:indexMetreLimit"
                  : "normative:indexMinuteLimit",
                { value: f.number(value.threshold, 0) },
              )}
              value={score === null ? <NoValue /> : f.number(score, 1)}
              unit={t("normative:indexPercentUnit")}
            />
            <p>
              {t(
                index.weighting === "population"
                  ? "normative:indexPopulationBasis"
                  : "normative:indexPointBasis",
              )}
            </p>
            {index.weighting === "population" ? <PopulationReference value={value} /> : null}
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
      <IndexMethod index={index} />
    </Card>
  )
}

function IndexUnavailable({ index }: { readonly index: RegionalIndex }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const messages: Readonly<Record<string, readonly [MessageKey, MessageKey]>> = {
    not_regulated: ["normative:indexNotRegulated", "normative:indexNotRegulatedNote"],
    model_unavailable: ["normative:indexModelUnavailable", "normative:indexModelUnavailableNote"],
    measurement_incompatible: [
      "normative:indexMeasurementIncompatible",
      "normative:indexMeasurementIncompatibleNote",
    ],
    local_selection_required: [
      "normative:indexLocalSelection",
      "normative:indexLocalSelectionNote",
    ],
  }
  const [title, description] = messages[index.status] ?? [
    "normative:indexNeedsMeasurement",
    "normative:indexNeedsMeasurementNote",
  ]
  return (
    <Card as="div" title={t("normative:indexTitle")} className={styles.index}>
      <EmptyState icon="info" title={t(title)} description={t(description)} />
      {index.basis?.thresholds.map((threshold) => (
        <p key={threshold}>
          {t(
            index.basis?.unit === "metres"
              ? "normative:indexPublishedMetreLimit"
              : "normative:indexPublishedMinuteLimit",
            { value: f.number(threshold, 0) },
          )}
        </p>
      ))}
      <IndexIntervals index={index} />
      <IndexMethod index={index} />
    </Card>
  )
}

const MODE_KEYS: Readonly<Record<string, MessageKey>> = {
  car: "normative:indexModes.car",
  walk: "normative:indexModes.walk",
  emergency_response: "normative:indexModes.emergency_response",
  pedestrian_transit: "normative:indexModes.pedestrian_transit",
  none: "normative:indexModes.none",
}

function IndexMethod({ index }: { readonly index: RegionalIndex }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const basis = index.basis
  if (!basis) return null
  return (
    <Disclosure title={t("normative:indexMethod")}>
      <div className={styles.method}>
        {index.status === "ready" ? <p>{t("normative:indexMethodNote")}</p> : null}
        <p>
          {t("normative:indexRequiredMode", {
            mode: t(MODE_KEYS[basis.required_mode] ?? "normative:indexModes.none"),
          })}
        </p>
        {basis.thresholds.length > 1 ? <p>{t("normative:indexThresholdVariants")}</p> : null}
        <IndexMeasurement index={index} />
        <p>{t("normative:indexAct", { act: basis.act, clause: basis.clause })}</p>
        <p>{t("normative:sourceEdition", { date: f.date(basis.edition_date) })}</p>
        <IndexReview index={index} />
        <ButtonLink to={basis.source_url} icon="external" variant="ghost">
          {t("normative:source")}
        </ButtonLink>
      </div>
    </Disclosure>
  )
}

const MUNICIPALITY_KEYS: Readonly<Record<string, MessageKey>> = {
  urban_okrug: "normative:indexMunicipalityTypes.urban_okrug",
  municipal_district: "normative:indexMunicipalityTypes.municipal_district",
  urban_settlement: "normative:indexMunicipalityTypes.urban_settlement",
  rural_settlement: "normative:indexMunicipalityTypes.rural_settlement",
}

function IndexIntervals({ index }: { readonly index: RegionalIndex }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <>
      {index.basis?.intervals.map((row) => (
        <p key={`${row.municipality_type}:${row.mode}:${row.profile}`}>
          {t("normative:indexInterval", {
            scope: t(MUNICIPALITY_KEYS[row.municipality_type] ?? "normative:indexRegion"),
            min: f.number(row.minimum, 0),
            max: f.number(row.maximum, 0),
            mode: t(
              row.mode === "transport"
                ? "normative:indexIntervalModes.transport"
                : "normative:indexIntervalModes.pedestrian_or_transport",
            ),
          })}
        </p>
      ))}
    </>
  )
}
