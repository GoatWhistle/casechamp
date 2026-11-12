import { useId } from "react"
import { useRegion } from "@/entities/region"
import type { RoadGraphState, ScenarioView, SummaryPart } from "@/entities/road-graph"
import type { ChatContext } from "@/shared/api/chat-stream"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { HelpTip, RowButton, Segmented } from "@/shared/ui"
import styles from "./road-scenario.module.css"
import { ScenarioHistory } from "./scenario-history"

const TOOLS = [
  { view: "criticality", label: "graph:tools.criticality" },
  { view: "improvement", label: "graph:tools.improvement" },
] as const

export interface ScenarioHomeProps {
  readonly roads: RoadGraphState
  readonly context: ChatContext
  readonly roadParts: readonly SummaryPart[]
  readonly linkParts: readonly SummaryPart[]
  readonly onView: (view: ScenarioView) => void
  readonly onOpenJob: (id: string) => void
}

export function ScenarioHome({
  roads,
  context,
  roadParts,
  linkParts,
  onView,
  onOpenJob,
}: ScenarioHomeProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const draftId = useId()
  const toolsId = useId()
  const summary = (parts: readonly SummaryPart[]) =>
    parts.length ? f.list(parts.map((part) => t(part.text, part.values))) : undefined
  return (
    <>
      <RegionTitle context={context} />
      <section className={styles.section} aria-labelledby={draftId}>
        <div className={styles.sectionHead}>
          <p id={draftId} className={styles.sectionTitle}>
            {t("graph:home.draft")}
          </p>
        </div>
        <ul className={styles.list}>
          <li>
            <RowButton
              chevron
              label={t("graph:home.roads")}
              meta={summary(roadParts) ?? t("graph:home.roadsEmpty")}
              onClick={() => onView("roads")}
            />
          </li>
          <li>
            <RowButton
              chevron
              label={t("graph:home.links")}
              meta={summary(linkParts) ?? t("graph:home.linksEmpty")}
              onClick={() => onView("links")}
            />
          </li>
          <li className={styles.settingRow}>
            <span className={styles.settingLabel}>
              {t("graph:scenario")}
              <HelpTip content={t("graph:method")} label={t("common:ui.hint")} />
            </span>
            <Segmented
              label={t("graph:scenario")}
              display="short"
              value={roads.draft.network}
              onChange={(network) => roads.editDraft({ network })}
              options={[
                { value: "road", label: t("graph:base"), short: t("graph:baseShort") },
                { value: "summer", label: t("graph:summer"), short: t("graph:summerShort") },
                { value: "winter", label: t("graph:winter"), short: t("graph:winterShort") },
              ]}
            />
          </li>
        </ul>
      </section>
      <ScenarioHistory roads={roads} region={context.region_id ?? null} onOpen={onOpenJob} />
      <section className={styles.section} aria-labelledby={toolsId}>
        <div className={styles.sectionHead}>
          <p id={toolsId} className={styles.sectionTitle}>
            {t("graph:home.tools")}
          </p>
        </div>
        <ul className={styles.list}>
          {TOOLS.map((tool) => (
            <li key={tool.view}>
              <RowButton chevron label={t(tool.label)} onClick={() => onView(tool.view)} />
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}

function RegionTitle({ context }: { readonly context: ChatContext }) {
  const { t } = useTranslation()
  const id = context.region_id ?? ""
  const region = useRegion(id, context.season ?? "summer")
  if (!id) return <p className={styles.regionMissing}>{t("graph:draft.pickRegion")}</p>
  return <p className={styles.region}>{region.data?.id === id ? region.data.name : null}</p>
}
