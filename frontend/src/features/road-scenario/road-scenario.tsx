import { useEffect, useRef } from "react"
import { type RoadGraphState, type ScenarioView, useScenarioView } from "@/entities/road-graph"
import type { ChatContext } from "@/shared/api/chat-stream"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, PanelView, ViewHeader } from "@/shared/ui"
import { LinkEditor } from "./link-editor"
import { RoadConnection } from "./road-connection"
import styles from "./road-scenario.module.css"
import { RoadSelection } from "./road-selection"
import { ScenarioFooter } from "./scenario-footer"
import { ScenarioHome } from "./scenario-home"
import { rejectionMessage } from "./scenario-payload"
import { ScenarioResult } from "./scenario-result"
import { SpeedPicker } from "./speed-picker"
import { useScenarioDraft } from "./use-scenario-draft"

export interface RoadScenarioProps {
  readonly roads: RoadGraphState
  readonly context: ChatContext
}

const TITLE: Readonly<Record<ScenarioView, MessageKey>> = {
  home: "graph:tab",
  roads: "graph:home.roads",
  links: "graph:home.links",
  connection: "graph:tools.connection",
  result: "graph:result.title",
  criticality: "graph:tools.criticality",
  improvement: "graph:tools.improvement",
}

export function RoadScenario({ roads, context }: RoadScenarioProps) {
  const { t } = useTranslation()
  const { view, setView } = useScenarioView()
  const regionId = context.region_id ?? null
  const draft = useScenarioDraft(roads, regionId)
  const count = roads.selected.length
  const seen = useRef(count)
  useEffect(() => {
    if (count > seen.current && view === "home") setView("roads")
    seen.current = count
  }, [count, view, setView])
  const header =
    view === "home" ? undefined : (
      <ViewHeader
        title={t(TITLE[view])}
        backLabel={t("graph:back")}
        onBack={() => setView("home")}
      />
    )
  const footer = (
    <ScenarioFooter
      parts={draft.parts}
      blocker={draft.blocker}
      pending={roads.submit.isPending}
      label={t("graph:calculate")}
      onRun={() => {
        if (draft.payload)
          roads.submit.mutate(draft.payload, { onSuccess: () => setView("result") })
      }}
    />
  )
  return (
    <Swap swapKey={view} as="div" className={styles.stage}>
      {view === "connection" ? (
        <RoadConnection
          roads={roads}
          regionId={regionId}
          busy={draft.busy}
          header={header}
          onDone={() => setView("result")}
        />
      ) : (
        <PanelView
          label={t(TITLE[view])}
          header={header}
          footer={view === "result" ? undefined : footer}
        >
          {view === "roads" ? (
            <>
              <RoadSelection roads={roads} />
              <SpeedPicker
                value={roads.draft.speed}
                onChange={(speed) => roads.editDraft({ speed })}
              />
            </>
          ) : view === "links" ? (
            <LinkEditor roads={roads} />
          ) : view === "result" ? (
            <ScenarioResult roads={roads} />
          ) : (
            <ScenarioHome
              roads={roads}
              context={context}
              roadParts={draft.roadParts}
              linkParts={draft.linkParts}
              onView={setView}
              onOpenJob={(id) => {
                roads.selectJob(id)
                setView("result")
              }}
            />
          )}
          <ScenarioError roads={roads} />
        </PanelView>
      )}
    </Swap>
  )
}

function ScenarioError({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  const rejection = rejectionMessage(roads.submit.error)
  if (rejection)
    return <Banner tone="danger" title={t("graph:links.rejected")} description={rejection} />
  if (roads.submit.isError || roads.statusError || roads.cancel.isError)
    return <Banner tone="danger" title={t("graph:requestError")} />
  return null
}
