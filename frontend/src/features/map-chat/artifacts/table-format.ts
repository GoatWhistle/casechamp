import type { ChatColumn, ChatRow } from "@/shared/api/chat-artifacts"
import type { Formatters, MessageKey, useTranslation } from "@/shared/i18n"

const MODES: Readonly<Record<string, MessageKey>> = {
  rail: "data:mode.rail",
  air: "data:mode.air",
  bus: "data:mode.bus",
  river: "data:mode.river",
  winter_road: "data:mode.winter_road",
  ferry: "data:mode.ferry",
  ice_crossing: "data:mode.ice_crossing",
  pontoon_bridge: "data:mode.pontoon_bridge",
}

const LABELS: Readonly<Record<string, MessageKey>> = {
  before: "chat:columns.before",
  after: "chat:columns.after",
  before_minutes: "chat:columns.beforeMinutes",
  after_minutes: "chat:columns.afterMinutes",
  lost_nearby: "chat:columns.lostNearby",
  delayed_residents: "chat:columns.delayedResidents",
  flow_pcu_h: "chat:columns.flowPcuH",
  queue_pcu: "chat:columns.queuePcu",
  time_loss_pcu_hours: "chat:columns.timeLossPcuHours",
  score_before: "chat:columns.scoreBefore",
  score_after: "chat:columns.scoreAfter",
  hours_before: "chat:columns.hoursBefore",
  hours_after: "chat:columns.hoursAfter",
  status_before: "chat:columns.statusBefore",
  status_after: "chat:columns.statusAfter",
  reachable_before: "chat:columns.reachableBefore",
  reachable_after: "chat:columns.reachableAfter",
  pair_count: "chat:columns.pairCount",
  disconnected_pairs: "chat:columns.disconnectedPairs",
  name: "chat:columns.name",
  time_multiplier: "chat:columns.timeMultiplier",
  delta: "chat:columns.delta",
  relative_change: "chat:columns.relativeChange",
  hansen: "chat:columns.hansen",
  population: "data:metric.population",
  links_season: "data:metric.links",
  settlements: "chat:columns.settlements",
  companies: "data:metric.companies",
  coverage: "data:network.coverageColumn",
  origin: "chat:columns.origin",
  destination: "chat:columns.destination",
  mode: "chat:columns.mode",
  frequency: "chat:columns.frequency",
}

const ROUTE_STATUSES: Readonly<Record<string, MessageKey>> = {
  reachable: "chat:routeStatus.reachable",
  unreachable: "chat:routeStatus.unreachable",
  unbound: "chat:routeStatus.unbound",
}

export const columnKey = (key: string): MessageKey => LABELS[key] ?? "chat:columns.value"

export function formatCell(
  column: ChatColumn,
  value: ChatRow[string] | undefined,
  f: Formatters,
): string {
  if (value === null || value === undefined) return ""
  if (typeof value !== "number") return value
  if (column.format === "percent") return f.percent(value, 1)
  return column.format === "integer" ? f.integer(value) : f.number(value, 1)
}

export type Translate = ReturnType<typeof useTranslation>["t"]

export function displayCell(
  column: ChatColumn,
  value: ChatRow[string] | undefined,
  f: Formatters,
  t: Translate,
) {
  if (value === null || value === undefined) return t("chat:missing")
  if (column.key === "mode" && value in MODES) return t(MODES[value] ?? "chat:missing")
  if (column.key === "status_before" || column.key === "status_after")
    return t(ROUTE_STATUSES[String(value)] ?? "chat:missing")
  return formatCell(column, value, f)
}

export function literal(value: string): string {
  return value.replace(/\s+/g, " ").replace(/([\\`*_{}[\]()<>#+.!|~-])/g, "\\$1")
}
