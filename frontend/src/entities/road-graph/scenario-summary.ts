import type { MessageKey } from "@/shared/i18n"
import type { IconName } from "@/shared/ui"

export interface SummaryPart {
  readonly id: string
  readonly icon: IconName
  readonly text: MessageKey
  readonly values: Readonly<Record<string, string | number>>
}

export interface ScenarioShape {
  readonly scenario: string
  readonly changes: readonly {
    readonly speed_factor?: number
    readonly closed?: boolean
    readonly lanes_total?: number | null
    readonly highway?: string | null
    readonly surface?: string | null
    readonly speed_kmh?: number | null
  }[]
  readonly links?: readonly unknown[] | undefined
  readonly addition?: { readonly travel_hours: number } | null | undefined
}

function roadsPart(changes: ScenarioShape["changes"]): SummaryPart | null {
  const count = changes.length
  if (!count) return null
  if (changes.every((change) => change.closed === true))
    return { id: "roads", icon: "route", text: "graph:summary.closed", values: { count } }
  if (
    changes.some(
      (change) =>
        change.lanes_total != null || change.highway || change.surface || change.speed_kmh != null,
    )
  )
    return { id: "roads", icon: "route", text: "graph:summary.profile", values: { count } }
  const factors = [...new Set(changes.map((change) => change.speed_factor))]
  const [factor] = factors
  if (factor === undefined || factors.length > 1)
    return { id: "roads", icon: "route", text: "graph:summary.roadsMixed", values: { count } }
  if (factor === 0)
    return { id: "roads", icon: "route", text: "graph:summary.closed", values: { count } }
  return {
    id: "roads",
    icon: "route",
    text: "graph:summary.roads",
    values: { count, change: Math.round((factor - 1) * 100) },
  }
}

export function scenarioParts(shape: ScenarioShape): SummaryPart[] {
  const parts: SummaryPart[] = []
  if (shape.addition)
    parts.push({
      id: "addition",
      icon: "link",
      text: "graph:summary.connection",
      values: { minutes: shape.addition.travel_hours * 60 },
    })
  const roads = roadsPart(shape.changes)
  if (roads) parts.push(roads)
  const links = shape.links?.length ?? 0
  if (links)
    parts.push({ id: "links", icon: "rail", text: "graph:summary.links", values: { count: links } })
  if (shape.scenario === "summer")
    parts.push({ id: "network", icon: "sun", text: "graph:summer", values: {} })
  if (shape.scenario === "winter")
    parts.push({ id: "network", icon: "snowflake", text: "graph:winter", values: {} })
  return parts
}

function precision(value: number): number {
  const size = Math.abs(value)
  if (size === 0 || size >= 1) return 2
  return Math.min(6, Math.ceil(-Math.log10(size)) + 1)
}

export function deltaDigits(value: number): number {
  return Math.max(2, precision(value))
}

export function signed(value: number, format: (value: number, digits?: number) => string): string {
  const text = format(Math.abs(value), precision(value))
  if (value > 0) return `+${text}`
  return value < 0 ? `−${text}` : text
}

export type DeltaTone = "gain" | "loss" | "flat"

export function deltaTone(value: number): DeltaTone {
  if (value > 0) return "gain"
  return value < 0 ? "loss" : "flat"
}
