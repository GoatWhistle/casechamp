import { useState } from "react"
import type { components } from "@/shared/api/schema.gen"
import type { TrafficRoad } from "@/shared/api/traffic"
import { useTrafficView } from "@/shared/hooks/use-traffic-view"
import { useTranslation } from "@/shared/i18n"
import { Button, HelpTip } from "@/shared/ui"
import styles from "./municipal-traffic.module.css"

type Request = components["schemas"]["MunicipalScenarioRequest"]

export function MunicipalSegmentActions({
  road,
  pending,
  onSubmit,
}: {
  readonly road: TrafficRoad
  readonly pending: boolean
  readonly onSubmit: (kind: Request["kind"], edges: number[]) => void
}) {
  const { t } = useTranslation()
  const [reverse, setReverse] = useState(false)
  const selected = reverse ? road.reverse_edge_index : road.edge_index
  if (road.edge_index == null) return null
  const both = [road.edge_index, road.reverse_edge_index].filter(
    (value): value is number => value != null,
  )
  return (
    <div className={styles.content}>
      <strong>{t("map:municipalTraffic.localSegment")}</strong>
      <p>{t(reverse ? "map:municipalTraffic.directionBA" : "map:municipalTraffic.directionAB")}</p>
      {road.reverse_edge_index != null ? (
        <Button variant="ghost" disabled={pending} onClick={() => setReverse(!reverse)}>
          {t("map:municipalTraffic.reverseDirection")}
        </Button>
      ) : null}
      <div className={styles.actions}>
        <Button
          disabled={pending || selected == null || road.shared_lane === true}
          onClick={() => selected != null && onSubmit("lane_closure", [selected])}
        >
          {t("map:municipalTraffic.closeLane")}
        </Button>
        <HelpTip
          label={t("map:municipalTraffic.closeLane")}
          content={t(
            road.shared_lane
              ? "map:municipalTraffic.sharedClosure"
              : "map:municipalTraffic.laneClosureHelp",
          )}
        />
        <Button variant="secondary" disabled={pending} onClick={() => onSubmit("closure", both)}>
          {t("map:municipalTraffic.closeSegment")}
        </Button>
      </div>
    </div>
  )
}

export function MunicipalSegmentSelection({
  baseline,
  regionId,
  municipalityId,
  pending,
  onSubmit,
}: {
  readonly baseline: components["schemas"]["MunicipalTrafficBaseline"]
  readonly regionId: string
  readonly municipalityId: string
  readonly pending: boolean
  readonly onSubmit: (request: Request) => void
}) {
  const view = useTrafficView()
  const road = view.job?.id === baseline.view.id ? view.selected : null
  if (!road) return null
  return (
    <MunicipalSegmentActions
      key={road.edge_index}
      road={road}
      pending={pending}
      onSubmit={(kind, edge_indices) =>
        onSubmit({
          baseline_id: baseline.baseline_id,
          region_id: regionId,
          municipality_id: municipalityId,
          kind,
          way_ids: [road.way_id],
          edge_indices,
        })
      }
    />
  )
}
