import { useState } from "react"
import type { components } from "@/shared/api"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Banner, Card, ErrorState, NumberField, Select, Skeleton, TextField } from "@/shared/ui"

type FireOriginBasis = NonNullable<components["schemas"]["AssessmentInput"]["origin_basis"]>

export function useFireScenario(enabled: boolean) {
  const [originBasis, setOriginBasis] = useState<FireOriginBasis>("settlements")
  const [speed, setSpeed] = useState("")
  const [assumption, setAssumption] = useState("")
  const number = Number(speed.replace(",", "."))
  const validSpeed = speed.trim() !== "" && Number.isFinite(number) && number > 0 && number <= 200
  const validAssumption = assumption.trim().length >= 8 && assumption.trim().length <= 500
  const profile =
    enabled && validSpeed && validAssumption
      ? { speed_kmh: number, assumption: assumption.trim() }
      : null
  return {
    originBasis,
    setOriginBasis,
    speed,
    setSpeed,
    assumption,
    setAssumption,
    validSpeed,
    profile,
    parameters: profile ? { fire_profile: profile, origin_basis: originBasis } : {},
    ready: !enabled || profile !== null,
  }
}

export function FireScenarioFields({
  state,
  enabled,
  objectCount,
  objectPending = false,
  objectError = false,
  onRetryObjects,
  destinationSelection = true,
}: {
  readonly destinationSelection?: boolean
  readonly objectCount?: number | undefined
  readonly objectPending?: boolean
  readonly objectError?: boolean
  readonly onRetryObjects?: (() => void) | undefined
  readonly enabled: boolean
  readonly state: ReturnType<typeof useFireScenario>
}) {
  const { t } = useTranslation()
  if (!enabled) return null
  return (
    <Card
      as="div"
      title={t("normative:fireScenarioTitle")}
      description={t("normative:fireScenarioNote")}
    >
      {destinationSelection ? (
        <FireDestinationFields
          state={state}
          count={objectCount}
          pending={objectPending}
          error={objectError}
          onRetry={onRetryObjects}
        />
      ) : (
        <p>{t("normative:settlementReferenceNote")}</p>
      )}
      <NumberField
        label={t("normative:fireSpeed")}
        value={state.speed}
        onChange={(event) => state.setSpeed(event.target.value)}
        hint={t("normative:fireSpeedHint")}
        error={state.speed !== "" && !state.validSpeed ? t("normative:fireSpeedError") : undefined}
      />
      <TextField
        label={t("normative:fireAssumption")}
        value={state.assumption}
        onChange={(event) => state.setAssumption(event.target.value)}
        maxLength={500}
        hint={t("normative:fireAssumptionHint")}
      />
    </Card>
  )
}

function FireDestinationFields({
  state,
  count,
  pending,
  error,
  onRetry,
}: {
  readonly state: ReturnType<typeof useFireScenario>
  readonly count: number | undefined
  readonly pending: boolean
  readonly error: boolean
  readonly onRetry: (() => void) | undefined
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <>
      <Select<FireOriginBasis>
        label={t("normative:originBasisLabel")}
        value={state.originBasis}
        onChange={state.setOriginBasis}
        options={[
          { value: "settlements", label: t("normative:originBases.settlements") },
          { value: "fire_objects", label: t("normative:originBases.fire_objects") },
        ]}
      />
      {state.originBasis === "settlements" ? (
        <p>{t("normative:settlementReferenceNote")}</p>
      ) : error ? (
        <ErrorState title={t("normative:fireObjectsError")} onRetry={onRetry} />
      ) : pending ? (
        <Skeleton lines={2} />
      ) : count ? (
        <p>{t("normative:fireObjectCount", { value: f.integer(count) })}</p>
      ) : (
        <Banner
          tone="neutral"
          title={t("normative:fireObjectsEmpty")}
          description={t("normative:fireObjectsEmptyHint")}
        />
      )}
    </>
  )
}

export function FireProfileNote({
  profile,
}: {
  readonly profile: components["schemas"]["FireProfileInput"] | null | undefined
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  return profile ? (
    <p>
      {t("normative:fireSavedProfile", {
        speed: f.number(profile.speed_kmh, 1),
        assumption: profile.assumption,
      })}
    </p>
  ) : null
}
