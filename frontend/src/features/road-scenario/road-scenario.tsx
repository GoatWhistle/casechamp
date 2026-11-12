import { type ReactNode, useEffect, useRef, useState } from "react"
import { type RoadGraphState, type ScenarioView, useScenarioView } from "@/entities/road-graph"
import type { ChatContext } from "@/shared/api/chat-stream"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Disclosure, PanelView, ViewHeader } from "@/shared/ui"
import { AppraisalForm } from "./appraisal/appraisal-form"
import { type Project, projectReady } from "./appraisal/appraisal-state"
import { LinkEditor } from "./link-editor"
import { RoadProfileEditor, type RoadProfileState } from "./profile/road-profile-editor"
import { profilePayload } from "./profile/road-profile-payload"
import styles from "./road-scenario.module.css"
import { RoadSelection } from "./road-selection"
import { ScenarioFooter } from "./scenario-footer"
import { ScenarioHome } from "./scenario-home"
import { rejectionMessage } from "./scenario-payload"
import { ScenarioResult } from "./scenario-result"
import { useScenarioDraft } from "./use-scenario-draft"

export interface RoadScenarioProps {
  readonly roads: RoadGraphState
  readonly context: ChatContext
  readonly stress?: ReactNode
}

const TITLE: Readonly<Record<ScenarioView, MessageKey>> = {
  home: "graph:tab",
  roads: "graph:home.roads",
  links: "graph:home.links",
  result: "graph:result.title",
  criticality: "graph:tools.criticality",
  improvement: "graph:tools.improvement",
}

export function RoadScenario({ roads, context, stress }: RoadScenarioProps) {
  const { t } = useTranslation()
  const { view, setView } = useScenarioView()
  const regionId = context.region_id ?? null
  const [appraisal, setAppraisal] = useState<Project | null>(null)
  const [profile, setProfile] = useState<RoadProfileState>({
    lanes: "",
    action: "lanes",
  })
  const draft = useScenarioDraft(roads, regionId, profilePayload(profile))
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
      blocker={!projectReady(appraisal) ? "appraisal:invalid" : draft.blocker}
      pending={roads.submit.isPending}
      label={t("graph:calculate")}
      onRun={() => {
        if (draft.payload)
          roads.submit.mutate(
            { ...draft.payload, appraisal },
            { onSuccess: () => setView("result") },
          )
      }}
    />
  )
  return (
    <Swap swapKey={view} as="div" className={styles.stage}>
      <PanelView
        label={t(TITLE[view])}
        header={header}
        footer={view === "result" ? undefined : footer}
      >
        <ScenarioBody
          view={view}
          roads={roads}
          context={context}
          draft={draft}
          profile={profile}
          setProfile={setProfile}
          setView={setView}
        />
        {view !== "result" ? (
          <AppraisalForm value={appraisal} regionId={regionId} onChange={setAppraisal} />
        ) : null}
        {view === "home" && stress ? (
          <Disclosure title={t("stress:title")}>{stress}</Disclosure>
        ) : null}
        <ScenarioError roads={roads} />
      </PanelView>
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

function ScenarioBody({
  view,
  roads,
  context,
  draft,
  profile,
  setProfile,
  setView,
}: {
  readonly view: ScenarioView
  readonly roads: RoadGraphState
  readonly context: ChatContext
  readonly draft: ReturnType<typeof useScenarioDraft>
  readonly profile: RoadProfileState
  readonly setProfile: (value: RoadProfileState) => void
  readonly setView: (value: ScenarioView) => void
}) {
  return view === "roads" ? (
    <>
      <RoadSelection roads={roads} />
      <RoadProfileEditor value={profile} onChange={setProfile} />
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
  )
}
