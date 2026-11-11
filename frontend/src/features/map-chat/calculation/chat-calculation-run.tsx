import { useEffect } from "react"
import type { AnalysisCommentary, ChatEntry } from "@/entities/chat"
import { useResultCommentary } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import { chatErrorKey } from "../chat-copy"
import { CalculationProgress } from "./calculation-progress"
import styles from "./chat-calculation-run.module.css"
import { ChatResultEvidence } from "./chat-result-evidence"
import { useCalculationJobs } from "./use-calculation-jobs"

export function ChatCalculationRun({
  message,
  autoReview,
  onCalculation,
  onCommentary,
  onSettled,
}: {
  readonly onSettled?: (() => void) | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly message: ChatEntry
  readonly autoReview: boolean
  readonly onCommentary:
    | ((messageId: string, key: string, value: AnalysisCommentary) => void)
    | undefined
}) {
  const { t } = useTranslation()
  const state = useCalculationJobs(message)
  const key = `calculation:${state.scenarioIds.join(",")}:${state.stressIds.join(",")}`
  const review = useResultCommentary(
    `${message.id}:${key}`,
    state.revision,
    {
      prompt: "Interpret the completed calculation",
      calculation_review: { scenario_ids: state.scenarioIds, stress_ids: state.stressIds },
    },
    message.commentaries?.[key],
    (value) => onCommentary?.(message.id, key, value),
    autoReview,
  )
  const settled = isSettled(state, review, autoReview)
  useEffect(() => {
    if (settled) onSettled?.()
  }, [settled, onSettled])
  const busy = !state.finished && !state.error
  const label = progressLabel(state.stage, busy, state.completed, review.complete || !autoReview, t)
  return (
    <div className={styles.run} data-calculation-run>
      {state.stressIds.length || busy ? (
        <CalculationProgress
          jobs={state.jobs}
          progress={state.progress}
          label={label}
          message={message}
          onCalculation={onCalculation}
        />
      ) : null}
      {!busy && !review.complete && !state.error && (autoReview || !state.stressIds.length) ? (
        <p className={styles.status} role="status">
          {label}
        </p>
      ) : null}
      {state.finished && state.completed < state.count ? (
        <p>{t("chat:calculationRun.partial", { count: state.completed, total: state.count })}</p>
      ) : null}
      {state.error ? (
        <p className={styles.error}>
          {t("chat:calculationRun.requestError")}{" "}
          <Button icon="retry" variant="ghost" onClick={state.retry}>
            {t("chat:retry")}
          </Button>
        </p>
      ) : null}
      <ChatResultEvidence
        review={review}
        scenarioIds={state.scenarioIds}
        stressIds={state.stressIds}
        finished={state.finished}
      />
      {review.error ? (
        <p className={styles.error}>
          {t(chatErrorKey(review.error))}{" "}
          <Button icon="retry" variant="ghost" onClick={review.retry}>
            {t("chat:retry")}
          </Button>
        </p>
      ) : null}
    </div>
  )
}

const stages = {
  queued: true,
  preparing: true,
  connectivity: true,
  baseline: true,
  routes: true,
  aggregating: true,
}
function stageName(stage: string): keyof typeof stages {
  return stage in stages ? (stage as keyof typeof stages) : "routes"
}

function progressLabel(
  stage: string,
  busy: boolean,
  completed: number,
  reviewed: boolean,
  t: ReturnType<typeof useTranslation>["t"],
) {
  if (busy) return t(`chat:calculationRun.stages.${stageName(stage)}`)
  if (!completed) return t("chat:calculationRun.failed")
  return t(reviewed ? "chat:calculationRun.done" : "chat:calculationRun.interpreting")
}

function isSettled(
  state: ReturnType<typeof useCalculationJobs>,
  review: AnalysisCommentary,
  autoReview: boolean,
) {
  if (state.error) return true
  if (!state.finished) return false
  return !state.completed || !autoReview || review.complete || Boolean(review.error)
}
