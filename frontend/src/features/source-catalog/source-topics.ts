import type { IconName } from "@/shared/ui"

export const TOPICS = ["network", "territory", "economy", "seasons", "other"] as const
export type SourceTopic = (typeof TOPICS)[number]
export type SourceUsage = "atlas" | "settlements" | "economy" | "calendar"

export const TOPIC_ICONS: Record<SourceTopic, IconName> = {
  network: "link",
  territory: "locate",
  economy: "building",
  seasons: "calendar",
  other: "database",
}

const GROUPS: Readonly<Record<string, SourceTopic>> = {
  "atlas-links": "network",
  "transport-operations": "network",
  "northern-delivery": "network",
  "traffic-surveys": "network",
  "atlas-settlements": "territory",
  "region-geometry": "territory",
  "nighttime-lights": "territory",
  rfsd: "economy",
  "fns-revexp": "economy",
  "seasonal-ugra": "seasons",
  "seasonal-closures": "seasons",
}

const USAGE: Readonly<Record<string, SourceUsage>> = {
  "atlas-links": "atlas",
  "region-geometry": "atlas",
  "atlas-settlements": "settlements",
  rfsd: "economy",
  "fns-revexp": "economy",
  "seasonal-ugra": "calendar",
}

export function sourceTopic(id: string): SourceTopic {
  return GROUPS[id] ?? "other"
}

export function sourceUsage(id: string): SourceUsage | undefined {
  return USAGE[id]
}
