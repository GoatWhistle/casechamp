import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import { type AnalysisCommentary, useResultCommentary } from "@/entities/chat"
import { api, unwrap } from "@/shared/api/client"
import { type TrafficJob, trafficJob, trafficTerminal } from "@/shared/api/traffic"
import { updateTrafficView } from "@/shared/hooks/use-traffic-view"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, ChatMessage, Meter } from "@/shared/ui"
import styles from "./traffic-card.module.css"
import { TrafficResults } from "./traffic-results"

export function TrafficCard({
  initial,
  autoReview,
  commentary,
  onCommentary,
}: {
  readonly initial: TrafficJob
  readonly autoReview: boolean
  readonly commentary?: AnalysisCommentary | undefined
  readonly onCommentary: (value: AnalysisCommentary) => void
}) {
  const { t } = useTranslation()
  const query = useQuery({
    queryKey: ["traffic-job", initial.id],
    queryFn: ({ signal }) => trafficJob(initial.id, signal),
    refetchInterval: (state) =>
      trafficTerminal(state.state.data?.status ?? initial.status) ? false : 1500,
  })
  const job = query.data ?? initial
  const busy = !trafficTerminal(job.status)
  const review = useResultCommentary(
    job.id,
    job.status === "completed" ? `${job.id}:${job.version}` : null,
    {
      prompt: "Interpret the road improvements",
      calculation_review: { scenario_ids: [], stress_ids: [], traffic_ids: [job.id] },
    },
    commentary,
    onCommentary,
    autoReview,
  )
  const cancel = useMutation({
    mutationFn: () =>
      unwrap(
        api.POST("/api/v1/traffic-jobs/{job_id}/cancel", { params: { path: { job_id: job.id } } }),
      ),
    onSuccess: () => {
      void query.refetch()
    },
  })
  useEffect(() => updateTrafficView(job), [job])
  return (
    <section className={styles.card} aria-label={t("traffic:title")} data-traffic-job={job.id}>
      <div className={styles.header}>
        <strong>{t(busy ? progressKey(job.stage) : "traffic:title")}</strong>
        {busy ? (
          <Button
            variant="ghost"
            icon="stop"
            size="compact"
            pending={cancel.isPending}
            onClick={() => cancel.mutate()}
          >
            {t("traffic:cancel")}
          </Button>
        ) : null}
      </div>
      {busy ? <Meter value={null} max={1} label={t(progressKey(job.stage))} thin /> : null}
      {query.isError || cancel.isError ? (
        <Banner
          tone="danger"
          title={t("traffic:requestError")}
          action={
            <Button variant="ghost" icon="retry" onClick={() => void query.refetch()}>
              {t("common:action.retry")}
            </Button>
          }
        />
      ) : null}
      {job.status === "failed" ? <Banner tone="danger" title={t(failureKey(job.error))} /> : null}
      {job.status === "completed" ? <TrafficResults job={job} /> : null}
      {job.status === "completed" && review.text ? (
        <ChatMessage speaker="assistant" text={review.text} label={t("chat:analysis.commentary")} />
      ) : null}
      {review.error ? (
        <Button variant="ghost" icon="retry" onClick={review.retry}>
          {t("traffic:retryCommentary")}
        </Button>
      ) : null}
    </section>
  )
}

function failureKey(error: string) {
  if (error === "traffic_scope_too_large") return "traffic:scopeTooLarge"
  if (error === "traffic_assignment_not_converged") return "traffic:notConverged"
  return "traffic:failed"
}

function progressKey(stage: string) {
  if (stage === "loading" || stage === "baseline") return "traffic:preparing"
  if (stage === "candidates") return "traffic:generating"
  if (stage === "comparing" || stage === "index_comparing") return "traffic:verifying"
  return "traffic:working"
}
