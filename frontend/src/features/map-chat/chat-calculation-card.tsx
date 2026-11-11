import { useEffect, useMemo, useRef } from "react"
import { ScenarioOutcome, useRoadJobs } from "@/entities/road-graph"
import type { CalculationHandler, ChatCalculation } from "@/shared/api/chat-calculation"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./chat-calculation.module.css"
import { corridorPaths } from "./corridor-paths"

export interface ChatCalculationCardProps {
  readonly autoFocus?: boolean
  readonly calculation: ChatCalculation
  readonly onShow?: CalculationHandler | undefined
}

export function ChatCalculationCard({
  calculation,
  onShow,
  autoFocus = true,
}: ChatCalculationCardProps) {
  const { t } = useTranslation()
  const label = calculationLabel(calculation)
  const title = t(label.key, { percent: label.percent })
  const shown = useRef(false)
  useEffect(() => {
    if (shown.current || !onShow || !autoFocus) return
    shown.current = true
    onShow(calculation)
  }, [calculation, onShow, autoFocus])
  const jobs = useRoadJobs(calculation.job_ids)
  const paths = useMemo(
    () => [...new Set(corridorPaths(calculation.corridor.lines))],
    [calculation.corridor.lines],
  )
  const busy = jobs.some(
    (query) => !query.isError && (!query.data || ["queued", "running"].includes(query.data.status)),
  )
  return (
    <section className={styles.calculation} aria-label={title}>
      <strong>
        {title}: {calculation.corridor.road_ref}
      </strong>
      <div className={styles.endpoints}>
        <span>{calculation.corridor.origin}</span>
        <span>{calculation.corridor.destination}</span>
      </div>
      <svg
        className={styles.preview}
        viewBox="0 0 320 160"
        role="img"
        aria-label={t("chat:calculation.geometry")}
      >
        <g className={styles.route}>
          {paths.map((path) => (
            <path key={path} d={path} />
          ))}
        </g>
        {busy ? (
          <g className={styles.pulse}>
            {paths.map((path) => (
              <path key={path} d={path} />
            ))}
          </g>
        ) : null}
      </svg>
      <p className={styles.note}>
        {t("chat:calculation.scope", { count: calculation.corridor.way_ids.length })}
      </p>
      <Button
        variant="secondary"
        icon="map"
        disabled={!onShow}
        onClick={(event) => onShow?.(calculation, event.detail === 0)}
      >
        {t("chat:calculation.show")}
      </Button>
      {jobs.map((query, index) => (
        <ScenarioOutcome
          key={calculation.job_ids[index]}
          query={query}
          fallbackName={calculation.corridor.regions[index]?.name}
        />
      ))}
      <p className={styles.note}>{t("chat:calculation.limit")}</p>
    </section>
  )
}

function calculationLabel(calculation: ChatCalculation): { key: MessageKey; percent: number } {
  const factors = [
    ...new Set(
      calculation.changes?.length ? calculation.changes.map((change) => change.speed_factor) : [0],
    ),
  ]
  const factor = factors.length === 1 ? factors[0] : undefined
  const percent = Math.round(Math.abs((factor ?? 1) - 1) * 10000) / 100
  if (factor === 0) return { key: "chat:calculation.title", percent }
  if (factor !== undefined && factor > 1) return { key: "chat:calculation.speedIncrease", percent }
  if (factor !== undefined && factor < 1) return { key: "chat:calculation.speedDecrease", percent }
  return { key: "chat:calculation.changeTitle", percent }
}
