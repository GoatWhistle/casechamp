import type { AccessRow } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink } from "@/shared/ui"

export function NormativePointEvidence({ point }: { readonly point: AccessRow }) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!point.qualification_source_url) return null
  return (
    <>
      {point.qualification_observed_at ? (
        <p>
          {t("normative:qualificationObserved", { date: f.date(point.qualification_observed_at) })}
        </p>
      ) : null}
      {point.threshold_source_url && point.threshold_minutes != null ? (
        <p>
          {t("normative:selectedThresholdMinutes", { value: f.number(point.threshold_minutes, 0) })}
        </p>
      ) : null}
      <ButtonLink to={point.qualification_source_url} icon="external" variant="ghost">
        {t("normative:qualificationSource")}
      </ButtonLink>
      {point.catchment_source_url ? (
        <ButtonLink to={point.catchment_source_url} icon="external" variant="ghost">
          {t("normative:catchmentSource")}
        </ButtonLink>
      ) : null}
      {point.travel_profile_source_url ? (
        <ButtonLink to={point.travel_profile_source_url} icon="external" variant="ghost">
          {t("normative:travelProfileSource")}
        </ButtonLink>
      ) : null}
      {point.measurement_method_source_url ? (
        <ButtonLink to={point.measurement_method_source_url} icon="external" variant="ghost">
          {t("normative:measurementMethodSource")}
        </ButtonLink>
      ) : null}
      {point.threshold_source_url ? (
        <ButtonLink to={point.threshold_source_url} icon="external" variant="ghost">
          {t("normative:thresholdSource")}
        </ButtonLink>
      ) : null}
    </>
  )
}
