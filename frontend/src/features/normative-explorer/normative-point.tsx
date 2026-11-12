import type { AccessRow } from "@/entities/normative"
import type { components } from "@/shared/api"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink, Card, Disclosure, NoValue, Segmented } from "@/shared/ui"
import { NormativePointEvidence } from "./evidence/normative-point-evidence"
import styles from "./normative-panel.module.css"
import { NormativeRouteDetail } from "./normative-route-detail"
import { NormativeRuleChecks } from "./normative-rule-checks"

export function NormativePoint({
  point,
  walking,
  runId,
  stage = "scenario",
  onStage,
  hasScenario = false,
  facilityName,
  library = false,
  fire = false,
  ruleChecks,
  regional = false,
}: {
  readonly regional?: boolean
  readonly ruleChecks?: readonly components["schemas"]["RuleCheckResponse"][] | undefined
  readonly fire?: boolean
  readonly library?: boolean
  readonly point: AccessRow
  readonly walking: boolean
  readonly runId?: string | null | undefined
  readonly stage?: NormativeRouteStage | undefined
  readonly onStage?: ((stage: NormativeRouteStage, instant?: boolean) => void) | undefined
  readonly hasScenario?: boolean | undefined
  readonly facilityName?: string | undefined
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const costLabel = pointCostKey(walking, fire)
  const value = walking ? point.distance_metres : point.minutes
  return (
    <Card as="div" title={point.name} className={styles.point}>
      <p>
        {t(regional ? "normative:regionalQualificationUnknown" : `normative:states.${point.state}`)}
      </p>
      {hasScenario && onStage ? (
        <Segmented<NormativeRouteStage>
          label={t("normative:routeStage")}
          value={stage}
          onChange={(next) => onStage(next, true)}
          options={[
            { value: "baseline", label: t("normative:baselineRoute") },
            { value: "scenario", label: t("normative:scenarioRoute") },
          ]}
        />
      ) : null}
      {facilityName ? <p>{t("normative:routeDestination", { name: facilityName })}</p> : null}
      {value == null ? (
        <NoValue />
      ) : (
        <p>
          {t(costLabel, {
            value: f.number(value, 1),
          })}
        </p>
      )}
      {point.origin_source_url ? <ObjectOriginSource point={point} /> : null}
      {library ? <LibraryTerritory point={point} /> : null}
      {fire ? <FireDestination point={point} /> : null}
      <NormativePointEvidence point={point} />
      <NormativeRuleChecks walking={walking} checks={ruleChecks} />
      {runId && point.routing_node != null && value != null ? (
        <NormativeRouteDetail regional={regional} runId={runId} originId={point.id} stage={stage} />
      ) : null}
      {runId && point.routing_node == null && value != null ? (
        <p className={styles.explanation}>{t("normative:routeRecalculate")}</p>
      ) : null}
      {point.uncertainty?.length ? (
        <Disclosure title={t("normative:unknownReasons")}>
          <ul>
            {point.uncertainty.map((reason) => (
              <li key={reason}>{t(`normative:uncertainty.${reason}`)}</li>
            ))}
          </ul>
        </Disclosure>
      ) : null}
    </Card>
  )
}

function ObjectOriginSource({ point }: { readonly point: AccessRow }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <Disclosure title={t("normative:objectOriginSource")}>
      <p>
        {t(
          point.origin_reference_status === "verified_object"
            ? "normative:objectReferenceVerified"
            : "normative:objectReferenceCandidate",
        )}
      </p>
      {point.origin_observed_at ? (
        <p>{t("normative:observed", { date: f.date(point.origin_observed_at) })}</p>
      ) : null}
      <ButtonLink to={point.origin_source_url ?? ""} icon="external" variant="ghost">
        {t("normative:openObjectSource")}
      </ButtonLink>
    </Disclosure>
  )
}

function LibraryTerritory({ point }: { readonly point: AccessRow }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <>
      <p>
        {point.threshold_minutes == null
          ? t("normative:territoryUnknown")
          : t("normative:territoryThreshold", { value: f.number(point.threshold_minutes, 0) })}
      </p>
      {point.municipality_code ? (
        <p>{t("normative:municipalityCode", { code: point.municipality_code })}</p>
      ) : null}
      {point.territory_verification_status === "encoded_parent_2024_assignment_unconfirmed" ? (
        <p className={styles.explanation}>{t("normative:encodedTerritoryCandidate")}</p>
      ) : null}
      {point.territory_source_url ? (
        <ButtonLink to={point.territory_source_url} icon="external" variant="ghost">
          {t("normative:territorySource")}
        </ButtonLink>
      ) : null}
      {point.territory_structure_source_url ? (
        <ButtonLink to={point.territory_structure_source_url} icon="external" variant="ghost">
          {t("normative:territoryStructureSource")}
        </ButtonLink>
      ) : null}
    </>
  )
}

function FireDestination({ point }: { readonly point: AccessRow }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <>
      <p>
        {point.threshold_minutes == null
          ? t("normative:fireSettlementUnknown")
          : t("normative:fireThresholdMinutes", { value: f.number(point.threshold_minutes, 0) })}
      </p>
      {point.territory_source_url ? (
        <ButtonLink to={point.territory_source_url} icon="external" variant="ghost">
          {t("normative:fireSettlementSource")}
        </ButtonLink>
      ) : null}
    </>
  )
}

function pointCostKey(walking: boolean, fire: boolean) {
  if (walking) return "normative:pointMetres"
  return fire ? "normative:firePointMinutes" : "normative:pointMinutes"
}
