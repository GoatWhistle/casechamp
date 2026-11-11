import { useId, useState } from "react"
import {
  deltaTone,
  type RoadGraphState,
  STATE_KEY,
  scenarioParts,
  scenarioState,
  signed,
} from "@/entities/road-graph"
import type { RoadJob } from "@/shared/api/road-graph"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { staggerStyle } from "@/shared/motion"
import { Button, RowButton } from "@/shared/ui"
import styles from "./road-scenario.module.css"

const PREVIEW = 4

export function ScenarioHistory({
  roads,
  region,
  onOpen,
}: {
  readonly roads: RoadGraphState
  readonly region: string | null
  readonly onOpen: (id: string) => void
}) {
  const { t } = useTranslation()
  const titleId = useId()
  const [expanded, setExpanded] = useState(false)
  const jobs = expanded ? roads.jobs : roads.jobs.slice(0, PREVIEW)
  if (!roads.jobs.length) return null
  return (
    <section className={styles.section} aria-labelledby={titleId}>
      <div className={styles.sectionHead}>
        <p id={titleId} className={styles.sectionTitle}>
          {t("graph:history")}
        </p>
      </div>
      <ul className={styles.list}>
        {jobs.map((job, index) => (
          <li
            key={job.id}
            className={index >= PREVIEW ? styles.entering : undefined}
            style={index >= PREVIEW ? staggerStyle(index - PREVIEW) : undefined}
          >
            <HistoryRow
              job={job}
              region={region}
              current={job.id === roads.job?.id}
              onOpen={onOpen}
            />
          </li>
        ))}
      </ul>
      {jobs.length < roads.jobs.length ? (
        <Button
          variant="ghost"
          size="compact"
          icon="chevron-down"
          className={styles.more}
          onClick={() => setExpanded(true)}
        >
          {t("graph:historyMore", { count: roads.jobs.length })}
        </Button>
      ) : null}
    </section>
  )
}

function HistoryRow({
  job,
  region,
  current,
  onOpen,
}: {
  readonly job: RoadJob
  readonly region: string | null
  readonly current: boolean
  readonly onOpen: (id: string) => void
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const parts = scenarioParts(job)
  const state = scenarioState(job)
  const result = job.result
  return (
    <RowButton
      current={current}
      label={f.list(parts.map((part) => t(part.text, part.values)))}
      detail={job.region_id === region ? undefined : job.region}
      meta={
        result ? (
          <span className={styles.tone} data-tone={deltaTone(result.delta)}>
            {signed(result.delta, f.number)}
          </span>
        ) : (
          t(STATE_KEY[state])
        )
      }
      onClick={() => onOpen(job.id)}
    />
  )
}
