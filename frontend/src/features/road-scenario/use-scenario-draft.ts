import { type RoadGraphState, type SummaryPart, scenarioParts } from "@/entities/road-graph"
import type { RoadChangeInput, RoadScenarioInput } from "@/shared/api/road-graph"
import type { MessageKey } from "@/shared/i18n"
import { needsSeason, scenarioPayload } from "./scenario-payload"

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
  readonly profileMissing: boolean
  readonly season: boolean
}): MessageKey | null {
  if (!input.regionId) return "graph:draft.pickRegion"
  if (input.busy) return "graph:draft.busy"
  if (input.empty) return "graph:draft.empty"
  if (input.profileMissing) return "graph:profile.invalid"
  return input.season ? "graph:draft.season" : null
}

export function useScenarioDraft(
  roads: RoadGraphState,
  regionId: string | null,
  profile?: Omit<RoadChangeInput, "way_id"> | null,
): ScenarioDraftState {
  const { network, links } = roads.draft
  const wayIds = roads.selected.map((road) => road.way_id)
  const busy = roads.submit.isPending || roads.jobs.some((job) => ACTIVE.has(job.status))
  const changes = profile ? wayIds.map(() => profile) : []
  const roadParts = scenarioParts({ scenario: "road", changes })
  const linkParts = scenarioParts({ scenario: "road", changes: [], links })
  const payload = scenarioPayload({
    regionId,
    scenario: network,
    wayIds,
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
      profileMissing: wayIds.length > 0 && !profile,
      season: needsSeason(links, network),
    }),
    busy,
  }
}
