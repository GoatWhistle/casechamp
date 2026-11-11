import { isApiError } from "@/shared/api"
import type {
  LinkChangeInput,
  LinkMode,
  RoadChangeInput,
  RoadScenarioInput,
  ScenarioNetwork,
  TransportLink,
} from "@/shared/api/road-graph"
import type { MessageKey } from "@/shared/i18n"

export const LINK_LIMIT = 30
export const SPEED_MAX = 300
const MODES: readonly LinkMode[] = [
  "rail",
  "air",
  "river",
  "ferry",
  "winter_road",
  "ice_crossing",
  "pontoon_bridge",
]

export const isLinkMode = (value: string): value is LinkMode =>
  (MODES as readonly string[]).includes(value)

export const linkKey = (link: LinkChangeInput) =>
  [link.action, link.network, link.mode, link.source, link.target].join("|")

export function removalOf(link: TransportLink): LinkChangeInput | null {
  if (!isLinkMode(link.mode) || (link.network !== "intercity" && link.network !== "local"))
    return null
  return {
    action: "remove",
    network: link.network,
    mode: link.mode,
    source: link.source,
    target: link.target,
  }
}

export function airportClosure(city: string): LinkChangeInput {
  return { action: "remove", network: "intercity", mode: "air", source: city.trim(), target: "*" }
}

export function additionOf(
  mode: "rail" | "air",
  source: string,
  target: string,
  hours: string,
): LinkChangeInput | MessageKey {
  const from = source.trim()
  const to = target.trim()
  const value = Number(hours.trim().replace(",", "."))
  if (!from || !to || from.toLocaleLowerCase("ru-RU") === to.toLocaleLowerCase("ru-RU"))
    return "graph:links.sameCity"
  if (!/^\d+([.,]\d+)?$/.test(hours.trim()) || value <= 0 || value > 72)
    return "graph:links.hoursError"
  return { action: "add", network: "intercity", mode, source: from, target: to, hours: value }
}

export function toggleLink(
  pending: readonly LinkChangeInput[],
  link: LinkChangeInput,
): readonly LinkChangeInput[] {
  const key = linkKey(link)
  if (pending.some((item) => linkKey(item) === key))
    return pending.filter((item) => linkKey(item) !== key)
  return pending.length < LINK_LIMIT ? [...pending, link] : pending
}

export function speedFactor(value: string): number | null {
  const text = value.trim()
  if (!/^\d+([.,]\d+)?$/.test(text)) return null
  const percent = Number(text.replace(",", "."))
  return percent <= SPEED_MAX ? percent / 100 : null
}

export function needsSeason(links: readonly LinkChangeInput[], scenario: ScenarioNetwork) {
  return scenario === "road" && links.some((link) => link.network === "local")
}

export function scenarioPayload(input: {
  readonly regionId: string | null | undefined
  readonly scenario: ScenarioNetwork
  readonly wayIds: readonly number[]
  readonly speed: number | null
  readonly links: readonly LinkChangeInput[]
  readonly profile?: Omit<RoadChangeInput, "way_id" | "speed_factor"> | null
}): RoadScenarioInput | null {
  if (!input.regionId || needsSeason(input.links, input.scenario)) return null
  if (input.profile === null && input.wayIds.length) return null
  const profile = input.profile ?? undefined
  const roads = input.speed === null && !profile ? [] : input.wayIds.slice(0, 50)
  if (!roads.length && !input.links.length) return null
  if (input.wayIds.length && input.speed === null && !profile) return null
  return {
    region_id: input.regionId,
    scenario: input.scenario,
    changes: roads.map((way_id) => ({
      way_id,
      speed_factor: profile ? 1 : (input.speed ?? 1),
      ...profile,
    })),
    links: input.links.slice(0, LINK_LIMIT),
  }
}

export function rejectionMessage(error: unknown): string | null {
  if (!isApiError(error) || (error.status !== 422 && error.status !== 400)) return null
  const detail = error.detail
  if (detail !== null && typeof detail === "object" && "message" in detail) {
    const { message } = detail
    if (typeof message === "string" && message.trim()) return message
  }
  return null
}
