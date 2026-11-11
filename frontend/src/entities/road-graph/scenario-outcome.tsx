import type { UseQueryResult } from "@tanstack/react-query"
import type { ReactNode } from "react"
import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Button, Meter, Skeleton, StatusBadge } from "@/shared/ui"
import { OutcomeResult } from "./outcome-result"
import styles from "./scenario-outcome.module.css"

const STATE_TONE = {
  queued: "neutral",
  running: "info",
  completed: "success",
  failed: "danger",
  cancelled: "neutral",
} as const

export type ScenarioState = keyof typeof STATE_TONE

export function scenarioState(job: RoadJob): ScenarioState {
  return job.status in STATE_TONE ? (job.status as ScenarioState) : "running"
}

export const STATE_KEY = {
  queued: "graph:outcome.queued",
  running: "graph:outcome.running",
  completed: "graph:outcome.done",
  failed: "graph:outcome.failed",
  cancelled: "graph:outcome.cancelled",
} as const

export interface ScenarioOutcomeProps {
  readonly query: UseQueryResult<RoadJob>
  readonly fallbackName?: string | undefined
  readonly detailed?: boolean | undefined
  readonly onCancel?: (() => void) | undefined
  readonly cancelling?: boolean | undefined
  readonly spec?: ReactNode
}

export function ScenarioOutcome({
  query,
  fallbackName,
  detailed = false,
  onCancel,
  cancelling = false,
  spec,
}: ScenarioOutcomeProps) {
  const { t } = useTranslation()
  const job = query.data
  if (query.isError)
    return (
      <Banner
        tone="danger"
        title={t("graph:requestError")}
        action={
          <Button variant="ghost" icon="retry" onClick={() => void query.refetch()}>
            {t("common:action.retry")}
          </Button>
        }
      />
    )
  if (!job)
    return (
      <section className={styles.outcome} data-detailed={detailed || undefined} aria-busy="true">
        <Skeleton lines={3} />
      </section>
    )
  const state = scenarioState(job)
  return (
    <section className={styles.outcome} data-detailed={detailed || undefined}>
      <div className={styles.head}>
        <strong className={styles.region}>{job.region || fallbackName}</strong>
        <Swap swapKey={state}>
          <StatusBadge tone={STATE_TONE[state]} label={t(STATE_KEY[state])} />
        </Swap>
      </div>
      {spec}
      <Swap swapKey={job.result ? "result" : state} as="div">
        {job.result ? (
          <OutcomeResult result={job.result} detailed={detailed} />
        ) : state === "failed" ? (
          <p className={styles.note}>
            {t(job.error === "baseline_mismatch" ? "graph:mismatch" : "graph:failed")}
          </p>
        ) : state === "cancelled" ? null : (
          <Progress job={job} onCancel={onCancel} cancelling={cancelling} />
        )}
      </Swap>
    </section>
  )
}

function Progress({
  job,
  onCancel,
  cancelling,
}: {
  readonly job: RoadJob
  readonly onCancel: (() => void) | undefined
  readonly cancelling: boolean
}) {
  const { t } = useTranslation()
  return (
    <div className={styles.progress} role="status">
      <Meter
        value={job.completed}
        max={Math.max(job.total, 1)}
        label={t("graph:outcome.progress")}
      />
      <div className={styles.progressRow}>
        <span className={styles.note}>
          {job.total > 0
            ? t("graph:outcome.count", { count: job.completed, total: job.total })
            : t("graph:outcome.preparing")}
        </span>
        {onCancel ? (
          <Button
            variant="ghost"
            size="compact"
            icon="stop"
            disabled={cancelling}
            onClick={onCancel}
          >
            {t("graph:cancel")}
          </Button>
        ) : null}
      </div>
    </div>
  )
}
