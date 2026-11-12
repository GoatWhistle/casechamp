import type { components } from "@/shared/api"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink, Disclosure, NoValue, StatusBadge } from "@/shared/ui"
import styles from "./normative-panel.module.css"

type Check = components["schemas"]["RuleCheckResponse"]

export function NormativeRuleChecks({
  walking,
  checks,
}: {
  readonly walking: boolean
  readonly checks: readonly Check[] | undefined
}) {
  const { t } = useTranslation()
  if (!walking) return null
  if (!checks?.length)
    return <p className={styles.explanation}>{t("normative:rulesRecalculate")}</p>
  return (
    <Disclosure title={t("normative:rulesTitle")}>
      <p className={styles.explanation}>{t("normative:rulesExplanation")}</p>
      {checks.map((check) => (
        <OneRule key={check.rule_id} check={check} />
      ))}
    </Disclosure>
  )
}

function OneRule({ check }: { readonly check: Check }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const unit = t(`normative:ruleUnits.${check.unit}`)
  return (
    <Disclosure title={t(`normative:ruleNames.${check.rule_id}`)}>
      <StatusBadge tone="neutral" icon="info" label={t(`normative:ruleResults.${check.result}`)} />
      <p>{t(`normative:ruleReasons.${check.reason}`)}</p>
      {check.applicability === "not_regulated" ? (
        <p>{t("normative:noNumericalLimit")}</p>
      ) : (
        <p>
          {t("normative:ruleLimit")}{" "}
          {check.threshold === null ? <NoValue /> : `${f.number(check.threshold, 0)} ${unit}`}
        </p>
      )}
      {check.candidate_thresholds.length ? (
        <p>
          {t("normative:ruleCandidates", {
            values: f.list(check.candidate_thresholds.map((value) => f.number(value, 0))),
            unit,
          })}
        </p>
      ) : null}
      {check.value !== null ? (
        <p>
          {t("normative:ruleMeasured", {
            value: f.number(check.value, 1),
            unit,
          })}
        </p>
      ) : null}
      <p>{t("normative:sourceEdition", { date: f.date(check.edition_date) })}</p>
      <ButtonLink to={check.source_url} icon="external" variant="ghost">
        {t("normative:source")}
      </ButtonLink>
      {check.facts_observed_at ? (
        <p>{t("normative:observed", { date: f.date(check.facts_observed_at) })}</p>
      ) : null}
      {check.facts_source_url ? (
        <ButtonLink to={check.facts_source_url} icon="external" variant="ghost">
          {t("normative:ruleFactsSource")}
        </ButtonLink>
      ) : null}
    </Disclosure>
  )
}
