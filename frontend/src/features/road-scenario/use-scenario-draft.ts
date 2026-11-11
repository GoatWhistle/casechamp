import { type RoadGraphState, type SummaryPart, scenarioParts } from "@/entities/road-graph"
import type { RoadChangeInput, RoadScenarioInput } from "@/shared/api/road-graph"
import type { MessageKey } from "@/shared/i18n"
import { needsSeason, scenarioPayload, speedFactor } from "./scenario-payload"

export interface ScenarioDraftState {
  readonly payload: RoadScenarioInput | null
  readonly parts: readonly SummaryPart[]
  readonly roadParts: readonly SummaryPart[]
  readonly linkParts: readonly SummaryPart[]
  readonly blocker: MessageKey | null
  readonly busy: boolean
}

const ACTIVE = new Set(["queued", "running"])

function blockerOf(input: {
  readonly regionId: string | null
  readonly busy: boolean
  readonly empty: boolean
  readonly speedMissing: boolean
  readonly season: boolean
}): MessageKey | null {
  if (!input.regionId) return "graph:draft.pickRegion"
  if (input.busy) return "graph:draft.busy"
  if (input.empty) return "graph:draft.empty"
  if (input.speedMissing) return "graph:draft.speed"
  return input.season ? "graph:draft.season" : null
}

export function useScenarioDraft(
  roads: RoadGraphState,
  regionId: string | null,
  profile?: Omit<RoadChangeInput, "way_id" | "speed_factor"> | null,
): ScenarioDraftState {
  const { speed, network, links } = roads.draft
  const factor = speedFactor(speed)
  const wayIds = roads.selected.map((road) => road.way_id)
  const busy =
    roads.submit.isPending ||
    roads.addConnection.isPending ||
    roads.jobs.some((job) => ACTIVE.has(job.status))
  const changes =
    factor === null && !profile
      ? []
      : wayIds.map(() => ({ speed_factor: profile ? 1 : (factor ?? 1), ...(profile ?? {}) }))
  const roadParts = scenarioParts({ scenario: "road", changes })
  const linkParts = scenarioParts({ scenario: "road", changes: [], links })
  const payload = scenarioPayload({
    regionId,
    scenario: network,
    wayIds,
    speed: factor,
    links,
    ...(profile !== undefined ? { profile } : {}),
  })
  return {
    payload: busy ? null : payload,
    parts: scenarioParts({ scenario: network, changes, links }),
    roadParts,
    linkParts,
    blocker: blockerOf({
      regionId,
      busy,
      empty: !wayIds.length && !links.length,
      speedMissing:
        wayIds.length > 0 && (profile === null || (profile === undefined && factor === null)),
      season: needsSeason(links, network),
    }),
    busy,
  }
}
