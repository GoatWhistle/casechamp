import { type ReactNode, useState } from "react"
import type { RoadGraphState } from "@/entities/road-graph"
import type { GraphLocation } from "@/shared/api/road-graph"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { Banner, PanelView, TextField } from "@/shared/ui"
import { AppraisalForm } from "./appraisal/appraisal-form"
import { type Project, projectReady } from "./appraisal/appraisal-state"
import { ConnectionPlace } from "./connection-place"
import styles from "./road-scenario.module.css"
import { ScenarioFooter } from "./scenario-footer"

const MAX_MINUTES = 4320

function blockerOf(input: {
  readonly regionId: string | null
  readonly busy: boolean
  readonly source: GraphLocation | null
  readonly target: GraphLocation | null
  readonly valid: boolean
}): MessageKey | null {
  if (!input.regionId) return "graph:draft.pickRegion"
  if (input.busy) return "graph:draft.busy"
  if (input.source?.node == null || input.target?.node == null) return "graph:connection.pick"
  if (input.source.node === input.target.node) return "graph:connection.same"
  return input.valid ? null : "graph:connection.invalidTime"
}

export function RoadConnection({
  roads,
  regionId,
  busy,
  header,
  onDone,
  appraisal,
  onAppraisal,
}: {
  readonly roads: RoadGraphState
  readonly regionId: string | null
  readonly busy: boolean
  readonly header: ReactNode
  readonly onDone: () => void
  readonly appraisal: Project | null
  readonly onAppraisal: (value: Project | null) => void
}) {
  const { t } = useTranslation()
  const [source, setSource] = useState<GraphLocation | null>(null)
  const [target, setTarget] = useState<GraphLocation | null>(null)
  const [minutes, setMinutes] = useState("")
  const duration = Number(minutes.replace(",", "."))
  const valid = /^\d+([.,]\d+)?$/.test(minutes.trim()) && duration > 0 && duration <= MAX_MINUTES
  const blocker = !projectReady(appraisal)
    ? "appraisal:invalid"
    : blockerOf({ regionId, busy, source, target, valid })
  const run = () => {
    if (blocker || !regionId || source?.node == null || target?.node == null) return
    roads.addConnection.mutate(
      {
        region_id: regionId,
        source_node: source.node,
        target_node: target.node,
        travel_hours: duration / 60,
        appraisal,
      },
      { onSuccess: onDone },
    )
  }
  return (
    <PanelView
      label={t("graph:tools.connection")}
      header={header}
      footer={
        <ScenarioFooter
          parts={[]}
          blocker={blocker}
          pending={roads.addConnection.isPending}
          label={t("graph:connection.calculate")}
          icon="link"
          onRun={run}
        />
      }
    >
      <section className={styles.form}>
        <p className={styles.hint}>{t("graph:connection.hint")}</p>
        <div className={styles.pair}>
          <ConnectionPlace
            label={t("graph:connection.from")}
            value={source}
            exclude={target?.node ?? null}
            onSelect={setSource}
          />
          <ConnectionPlace
            label={t("graph:connection.to")}
            value={target}
            exclude={source?.node ?? null}
            onSelect={setTarget}
          />
        </div>
        <TextField
          label={t("graph:connection.minutes")}
          value={minutes}
          inputMode="decimal"
          suffix={t("graph:connection.minutesUnit")}
          onChange={(event) => setMinutes(event.target.value)}
          error={minutes && !valid ? t("graph:connection.invalidTime") : undefined}
        />
      </section>
      <AppraisalForm value={appraisal} regionId={regionId} onChange={onAppraisal} />
      {roads.addConnection.isError ? (
        <Banner tone="danger" title={t("graph:requestError")} />
      ) : null}
    </PanelView>
  )
}
