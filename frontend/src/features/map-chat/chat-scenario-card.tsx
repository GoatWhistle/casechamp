import { RoadMoney, ScenarioOutcome, useRoadJobs } from "@/entities/road-graph"
import type { ChatScenario } from "@/shared/api/chat-scenario"
import { useTranslation } from "@/shared/i18n"
import { Button, Icon } from "@/shared/ui"
import styles from "./chat-calculation.module.css"

const KIND_ICON = {
  speed: "arrow-up",
  slowdown: "arrow-down",
  closure: "error",
  roads: "route",
  connection: "link",
  links: "whatif",
} as const

export interface ChatScenarioCardProps {
  readonly scenario: ChatScenario
  readonly onShow?: ((jobId: string) => void) | undefined
}

export function ChatScenarioCard({ scenario, onShow }: ChatScenarioCardProps) {
  const { t } = useTranslation()
  const jobs = useRoadJobs(scenario.job_ids)
  const first = scenario.job_ids[0]
  return (
    <section className={styles.calculation} aria-label={t("chat:scenario.label")}>
      <p className={styles.title}>
        <Icon name={KIND_ICON[scenario.kind]} size="sm" />
        {t(`chat:scenario.kind.${scenario.kind}`)}
      </p>
      {jobs.map((query, index) => (
        <div key={scenario.job_ids[index]} className={styles.job}>
          <ScenarioOutcome query={query} />
          {query.data ? <RoadMoney job={query.data} /> : null}
        </div>
      ))}
      {onShow && first && scenario.kind === "connection" ? (
        <Button variant="ghost" icon="map" onClick={() => onShow(first)}>
          {t("chat:scenario.show")}
        </Button>
      ) : null}
    </section>
  )
}
