import type { RoadJob } from "@/shared/api/road-graph"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Icon } from "@/shared/ui"
import styles from "./scenario-outcome.module.css"
import { deltaDigits, deltaTone, signed } from "./scenario-summary"
import { SettlementShifts } from "./settlement-shifts"

type Result = NonNullable<RoadJob["result"]>

const PREVIEW = 3
const DETAILED = 8

export function OutcomeResult({
  result,
  detailed,
}: {
  readonly result: Result
  readonly detailed: boolean
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const tone = deltaTone(result.delta)
  const digits = deltaDigits(result.delta)
  return (
    <div className={styles.result}>
      <div className={styles.summary}>
        <span className={styles.indexLabel}>{t("graph:outcome.index")}</span>
        <span className={styles.figure}>
          <span className={styles.delta} data-tone={tone}>
            {signed(result.delta, f.number)}
          </span>
          {result.relative_percent == null ? null : (
            <span className={styles.percent} data-tone={tone}>
              {t("graph:outcome.percent", { value: signed(result.relative_percent, f.number) })}
            </span>
          )}
        </span>
        <span className={styles.change} aria-hidden="true">
          <span>{f.number(result.before, digits)}</span>
          <Icon name="arrow-right" size="sm" className={styles.arrow} />
          <span>{f.number(result.after, digits)}</span>
        </span>
        <span className="visually-hidden">{t("graph:outcome.change", result)}</span>
      </div>
      {result.affected_settlements ? (
        <p className={styles.note}>
          {t("graph:outcome.affected", { count: result.affected_settlements })}
        </p>
      ) : null}
      <SettlementShifts
        effects={result.settlement_effects ?? []}
        limit={detailed ? DETAILED : PREVIEW}
        expandable={detailed}
      />
      {detailed ? <OutcomeEvidence result={result} /> : null}
    </div>
  )
}

function OutcomeEvidence({ result }: { readonly result: Result }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const items = [
    { id: "population", label: t("graph:outcome.population"), value: f.integer(result.population) },
    {
      id: "settlements",
      label: t("graph:outcome.settlements"),
      value: f.integer(result.settlements),
    },
    ...(result.changed_edges
      ? [{ id: "edges", label: t("graph:outcome.edges"), value: f.integer(result.changed_edges) }]
      : []),
    {
      id: "elapsed",
      label: t("graph:outcome.elapsed"),
      value: t("graph:outcome.seconds", { value: result.elapsed_seconds }),
    },
  ]
  return (
    <dl className={styles.evidence}>
      {items.map((item) => (
        <div key={item.id} className={styles.fact}>
          <dt className={styles.factLabel}>{item.label}</dt>
          <dd className={styles.factValue}>{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
