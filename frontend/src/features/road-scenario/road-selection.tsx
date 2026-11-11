import { useId, useState } from "react"
import type { RoadGraphState } from "@/entities/road-graph"
import type { RoadSegment } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { staggerStyle } from "@/shared/motion"
import { Banner, Button, RowButton, Skeleton } from "@/shared/ui"
import styles from "./road-scenario.module.css"

const PREVIEW = 6

interface RoadGroup {
  readonly name: string
  readonly segments: readonly RoadSegment[]
  readonly selected: number
}

function groupRoads(
  selected: readonly RoadSegment[],
  visible: readonly RoadSegment[],
): RoadGroup[] {
  const chosen = new Set(selected.map((road) => road.way_id))
  const order: string[] = []
  const byName = new Map<string, Map<number, RoadSegment>>()
  for (const road of [...selected, ...visible]) {
    const group = byName.get(road.name) ?? new Map<number, RoadSegment>()
    if (!byName.has(road.name)) order.push(road.name)
    group.set(road.way_id, road)
    byName.set(road.name, group)
  }
  return order.map((name) => {
    const segments = [...(byName.get(name)?.values() ?? [])]
    return { name, segments, selected: segments.filter((road) => chosen.has(road.way_id)).length }
  })
}

export function RoadSelection({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  const titleId = useId()
  const [expanded, setExpanded] = useState(false)
  const groups = groupRoads(roads.selected, roads.view.data?.segments ?? [])
  const shown = expanded ? groups : groups.slice(0, PREVIEW)
  const chosen = new Set(roads.selected.map((road) => road.way_id))
  const toggle = (group: RoadGroup) => {
    const all = group.selected === group.segments.length
    for (const road of group.segments) if (all || !chosen.has(road.way_id)) roads.onRoad(road)
  }
  return (
    <section className={styles.section} aria-labelledby={titleId}>
      <div className={styles.sectionHead}>
        <p id={titleId} className={styles.sectionTitle}>
          {t("graph:roads.title")}
        </p>
        {roads.selected.length ? (
          <span className={styles.sectionMeta}>
            {t("graph:roads.selected", { count: roads.selected.length })}
          </span>
        ) : null}
      </div>
      <RoadState roads={roads} empty={!groups.length} />
      {groups.length ? (
        <ul
          className={styles.list}
          data-stale={roads.view.isFetching || roads.rendering || undefined}
        >
          {shown.map((group, index) => (
            <li
              key={group.name}
              className={index >= PREVIEW ? styles.entering : undefined}
              style={index >= PREVIEW ? staggerStyle(index - PREVIEW) : undefined}
            >
              <RowButton
                icon="plus"
                pressed={group.selected > 0}
                label={group.name || t("graph:roads.unnamed")}
                detail={
                  group.selected > 0 && group.selected < group.segments.length
                    ? t("graph:roads.partial", {
                        count: group.selected,
                        total: group.segments.length,
                      })
                    : undefined
                }
                meta={
                  group.segments.length > 1
                    ? t("graph:roads.parts", { count: group.segments.length })
                    : undefined
                }
                onClick={() => toggle(group)}
              />
            </li>
          ))}
        </ul>
      ) : null}
      {shown.length < groups.length ? (
        <Button
          variant="ghost"
          size="compact"
          icon="chevron-down"
          className={styles.more}
          onClick={() => setExpanded(true)}
        >
          {t("graph:roads.more", { count: groups.length - shown.length })}
        </Button>
      ) : null}
      <p className={styles.hint}>{t(hintKey(roads.view.data?.detail))}</p>
    </section>
  )
}

function RoadState({ roads, empty }: { readonly roads: RoadGraphState; readonly empty: boolean }) {
  const { t } = useTranslation()
  if (!roads.enabled)
    return (
      <Banner
        tone="info"
        title={t("graph:roads.layerOff")}
        action={
          <Button variant="secondary" icon="route" onClick={() => roads.setEnabled(true)}>
            {t("graph:roads.layerOn")}
          </Button>
        }
      />
    )
  if (roads.view.isError)
    return (
      <Banner
        tone="danger"
        title={t("graph:loadError")}
        action={
          <Button variant="secondary" icon="retry" onClick={() => roads.view.refetch()}>
            {t("common:action.retry")}
          </Button>
        }
      />
    )
  if (roads.view.isLoading || (!roads.view.data && empty)) return <Skeleton lines={3} />
  return empty ? <p className={styles.hint}>{t("graph:roads.none")}</p> : null
}

function hintKey(detail: string | undefined) {
  return detail && detail !== "all" ? "graph:roads.zoomHint" : "graph:roads.mapHint"
}
