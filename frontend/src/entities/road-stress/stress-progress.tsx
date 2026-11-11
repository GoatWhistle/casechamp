import type { StressJob } from "@/shared/api/road-stress"
import { useTranslation } from "@/shared/i18n"
import { Button, Disclosure, ErrorState } from "@/shared/ui"

export function StressProgress({
  job,
  busy,
  pending,
  cancel,
}: {
  readonly job: StressJob
  readonly busy: boolean
  readonly pending: boolean
  readonly cancel: () => void
}) {
  const { t } = useTranslation()
  if (job.status === "completed") return null
  return (
    <>
      <p role="status" aria-live="polite">
        {t("stress:progress", {
          stage: t(`stress:stages.${stageName(job.stage)}`),
          done: job.completed,
          total: job.total,
        })}
      </p>
      {busy ? (
        <Button icon="x" variant="secondary" disabled={pending} onClick={cancel}>
          {t("stress:cancel")}
        </Button>
      ) : null}
      {job.status === "failed" ? <ErrorState title={t("stress:error")} /> : null}
    </>
  )
}
export function StressMethod({ job }: { readonly job: StressJob }) {
  const { t } = useTranslation()
  return (
    <Disclosure title={t("stress:method")}>
      <p>{t("stress:limits")}</p>
      <p>{t("stress:mapPoints")}</p>
      <p>{t("stress:coverage", { points: job.points, unbound: job.unbound_points })}</p>
      <p>{t("stress:preexisting", { count: job.preexisting_isolated_points ?? 0 })}</p>
    </Disclosure>
  )
}
const stages = {
  preparing: true,
  connectivity: true,
  baseline: true,
  routes: true,
  aggregating: true,
  completed: true,
  cancelled: true,
  interrupted: true,
}
function stageName(stage: string): keyof typeof stages {
  return stage in stages ? (stage as keyof typeof stages) : "preparing"
}
