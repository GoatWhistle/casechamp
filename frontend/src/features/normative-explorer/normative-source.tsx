import type { Assessment, Criterion } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink, Disclosure } from "@/shared/ui"
import styles from "./normative-panel.module.css"

export function NormativeSource({
  criterion: currentCriterion,
  result,
}: {
  readonly criterion: Criterion | undefined
  readonly result?: Assessment | null | undefined
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const criterion = result?.criterion ?? currentCriterion
  if (!criterion) return null
  return (
    <Disclosure title={t("normative:sourceOpen")}>
      <p>{t(`normative:acts.${criterion.act as "178"}`)}</p>
      <p>{t("normative:clause", { clause: criterion.clause })}</p>
      <CriterionThreshold criterion={criterion} />
      {result ? (
        <>
          {result.saved_at ? (
            <p>{t("normative:savedAt", { date: f.dateTime(result.saved_at) })}</p>
          ) : null}
          {result.qualification_as_of ? (
            <p>
              {t("normative:qualificationAsOf", { date: f.dateTime(result.qualification_as_of) })}
            </p>
          ) : null}
          <Disclosure title={t("normative:runDetails")}>
            <p>{t("normative:modelRevision", { version: result.model_revision })}</p>
            <p className={styles.explanation}>
              {t("normative:graphRevision", { version: result.graph_fingerprint })}
            </p>
          </Disclosure>
        </>
      ) : null}
      {criterion.act === "132n" ? <p>{t("normative:medicalAdjustment")}</p> : null}
      <p>{t("normative:sourceEdition", { date: f.date(criterion.edition_date) })}</p>
      <p className={styles.explanation}>{t(methodKey(criterion))}</p>
      {criterion.mode === "car" || criterion.service === "library" ? (
        <p className={styles.explanation}>{t("normative:attribution")}</p>
      ) : null}
      <ButtonLink to={criterion.source_url} icon="external" variant="ghost">
        {t("normative:source")}
      </ButtonLink>
    </Disclosure>
  )
}

function CriterionThreshold({ criterion }: { readonly criterion: Criterion }) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (["N03", "N04", "N07", "N09"].includes(criterion.id)) {
    return <p>{t(`normative:thresholdDetails.${criterion.id as "N03"}`)}</p>
  }
  return (
    <p>
      {t(
        criterion.act === "132n"
          ? "normative:medicalFederalThreshold"
          : "normative:thresholdMinutes",
        { value: f.number(criterion.threshold, 0) },
      )}
    </p>
  )
}

function methodKey(criterion: Criterion) {
  if (criterion.service === "fire") return "normative:fireMethod"
  return criterion.mode === "walk" ? "normative:walkingMethod" : "normative:caution"
}
