import { useEffect, useId } from "react"
import { type AnalysisCommentary, useAnalysisCommentary } from "@/entities/chat"
import { useAnalysisJob } from "@/entities/road-analysis"
import type { AnalysisJob } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, ChatMessage, Meter } from "@/shared/ui"
import { chatErrorKey } from "../chat-copy"
import styles from "./chat-analysis.module.css"

function failureKey(job: AnalysisJob) {
  return job.results.length ? "analysis:failed" : "analysis:failedEmpty"
}

export function ChatAnalysisCard({
  analysis,
  commentary,
  onCommentary,
  onSettled,
  autoReview = true,
}: {
  readonly autoReview?: boolean
  readonly onSettled?: (() => void) | undefined
  readonly analysis: AnalysisJob
  readonly commentary?: AnalysisCommentary | undefined
  readonly onCommentary?: ((value: AnalysisCommentary) => void) | undefined
}) {
  const { t } = useTranslation()
  const titleId = useId()
  const query = useAnalysisJob(analysis)
  const job = query.data
  const busy = ["queued", "running", "cancelling"].includes(job.status)
  const finished = ["paused", "completed"].includes(job.status)
  const revision =
    finished && job.compatible
      ? `${job.batch_target}:${job.results.length}:${job.failures.length}`
      : null
  const review = useAnalysisCommentary(job.id, revision, commentary, onCommentary, autoReview)
  const settled =
    query.isError ||
    (!busy &&
      (!finished || !job.compatible || !autoReview || review.complete || Boolean(review.error)))
  useEffect(() => {
    if (settled) onSettled?.()
  }, [settled, onSettled])
  const labels: Record<string, string> = {
    queued: t("analysis:queued"),
    running: t("analysis:verifying"),
    cancelling: t("analysis:cancelling"),
    paused: t("analysis:batchComplete"),
    completed: t("analysis:complete"),
    failed: t(failureKey(job)),
    cancelled: t("analysis:cancelled"),
    interrupted: t("analysis:interrupted"),
  }
  return (
    <section className={styles.analysis} aria-labelledby={titleId}>
      <strong id={titleId}>
        {t(`analysis:${job.mode}`)}: {job.region}
      </strong>
      <p role="status">{labels[job.status] ?? t("analysis:preparing")}</p>
      <p className={styles.note}>
        {t("analysis:checked", {
          count: job.results.length + job.failures.length,
          total: Math.min(job.batch_target, job.candidate_count || job.batch_target),
        })}
      </p>
      {busy && job.total > 1 ? (
        <Meter value={job.completed} max={job.total} label={t("analysis:stageProgress")} />
      ) : null}
      {query.isError ? (
        <Banner
          tone="danger"
          title={t("analysis:requestError")}
          action={
            <Button icon="retry" onClick={() => query.refetch()}>
              {t("analysis:retry")}
            </Button>
          }
        />
      ) : null}
      {!job.compatible ? <p>{t("analysis:incompatible")}</p> : null}
      {review.text ? (
        <ChatMessage speaker="assistant" text={review.text} label={t("chat:analysis.commentary")} />
      ) : null}
      {autoReview && finished && !review.complete && !review.error && job.compatible ? (
        <p role="status" className={styles.note}>
          {t("chat:analysis.commenting")}
        </p>
      ) : null}
      {review.error ? (
        <Banner
          tone="danger"
          title={t(chatErrorKey(review.error))}
          action={
            <Button icon="retry" onClick={review.retry}>
              {t("chat:retry")}
            </Button>
          }
        />
      ) : null}
    </section>
  )
}
