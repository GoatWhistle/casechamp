import { ScenarioOutcome, useRoadJobs } from "@/entities/road-graph"
import type { ChatScenario } from "@/shared/api/chat-scenario"
import { useTranslation } from "@/shared/i18n"
import { Icon } from "@/shared/ui"
import styles from "./chat-calculation.module.css"

const KIND_ICON = {
  speed: "arrow-up",
  slowdown: "arrow-down",
  closure: "error",
  roads: "route",
  connection: "link",
  links: "whatif",
} as const

export function ChatScenarioCard({ scenario }: { readonly scenario: ChatScenario }) {
  const { t } = useTranslation()
  const jobs = useRoadJobs(scenario.job_ids)
  return (
    <section className={styles.calculation} aria-label={t("chat:scenario.label")}>
      <p className={styles.title}>
        <Icon name={KIND_ICON[scenario.kind]} size="sm" />
        {t(`chat:scenario.kind.${scenario.kind}`)}
      </p>
      {jobs.map((query, index) => (
        <ScenarioOutcome key={scenario.job_ids[index]} query={query} />
      ))}
    </section>
  )
}
