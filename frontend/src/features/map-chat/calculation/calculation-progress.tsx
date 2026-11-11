import type { ChatEntry } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { RoadJob } from "@/shared/api/road-graph"
import type { StressJob } from "@/shared/api/road-stress"
import { useTranslation } from "@/shared/i18n"
import { Meter } from "@/shared/ui"
import { CalculationName } from "./calculation-name"
import styles from "./chat-calculation-run.module.css"
import { ChatResultMap } from "./chat-result-map"

const phases = ["connectivity", "baseline", "routes", "aggregating"] as const

export function CalculationProgress({
  jobs,
  progress,
  label,
  message,
  onCalculation,
}: {
  readonly message: ChatEntry
  readonly onCalculation?: CalculationHandler | undefined
  readonly jobs: readonly (RoadJob | StressJob)[]
  readonly progress: number | null
  readonly label: string
}) {
  const { t } = useTranslation()
  const stress = jobs.filter((job): job is StressJob => "stage" in job)
  if (!stress.length)
    return (
      <>
        <div className={styles.status}>
          <span>{label}</span>
          <strong>
            {t("chat:calculationRun.percent", {
              value: Math.floor(
                jobs.length && jobs.every((job) => job.status === "completed")
                  ? 100
                  : (progress ?? 0),
              ),
            })}
          </strong>
        </div>
        <Meter thin label={label} value={progress} max={100} />
      </>
    )
  return (
    <div className={styles.jobs}>
      {stress.map((job, index) => {
        const phase = (phases as readonly string[]).indexOf(job.stage)
        const done = job.status === "completed"
        const failed = ["failed", "cancelled"].includes(job.status)
        const active = !done && !failed
        const percent = done
          ? 100
          : Math.min(100, Math.max(0, Math.floor((job.completed / Math.max(1, job.total)) * 100)))
        const title = t("chat:calculationRun.job", { index: index + 1 })
        const stage = t(stageKey(job))
        return (
          <section key={job.id} className={styles.job} aria-label={title}>
            <div className={styles.status}>
              <CalculationName id={job.id} index={index + 1} />
              <strong>
                {t(done ? "chat:calculationRun.percent" : "chat:calculationRun.phasePercent", {
                  value: percent,
                })}
              </strong>
            </div>
            {active ? (
              <ol className={styles.phases} aria-label={t("chat:calculationRun.phases")}>
                {phases.map((name, step) => (
                  <li
                    key={name}
                    data-state={step < phase ? "done" : step === phase ? "active" : "waiting"}
                    aria-current={step === phase ? "step" : undefined}
                  >
                    {t(`chat:calculationRun.phaseNames.${name}`)}
                  </li>
                ))}
              </ol>
            ) : null}
            {active ? <Meter thin label={`${title}: ${stage}`} value={percent} max={100} /> : null}
            <div className={styles.status}>
              <span>{stage}</span>
              {active ? (
                <span>
                  {t("chat:calculationRun.stageCount", { count: job.completed, total: job.total })}
                </span>
              ) : null}
            </div>
            <ChatResultMap
              message={{ ...message, stressTests: [job], calculations: [] }}
              onCalculation={onCalculation}
              autoFocus={false}
            />
          </section>
        )
      })}
    </div>
  )
}

function stageKey(job: StressJob) {
  if (job.status === "completed") return "chat:calculationRun.done" as const
  if (["failed", "cancelled"].includes(job.status)) return "chat:calculationRun.failed" as const
  const phase = phases.find((name) => name === job.stage) ?? "preparing"
  return `chat:calculationRun.stages.${phase}` as const
}
