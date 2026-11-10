import type { LinkChange } from "@/shared/api/road-graph"
import type { MessageKey } from "@/shared/i18n"

type ModeKeys = Readonly<Record<string, MessageKey>>

const ADD: ModeKeys = {
  rail: "graph:links.add.rail",
  air: "graph:links.add.air",
  river: "graph:links.add.river",
  ferry: "graph:links.add.ferry",
  winter_road: "graph:links.add.winter_road",
  ice_crossing: "graph:links.add.ice_crossing",
  pontoon_bridge: "graph:links.add.pontoon_bridge",
}
const REMOVE: ModeKeys = {
  rail: "graph:links.remove.rail",
  air: "graph:links.remove.air",
  river: "graph:links.remove.river",
  ferry: "graph:links.remove.ferry",
  winter_road: "graph:links.remove.winter_road",
  ice_crossing: "graph:links.remove.ice_crossing",
  pontoon_bridge: "graph:links.remove.pontoon_bridge",
}
const REMOVE_ALL: ModeKeys = {
  rail: "graph:links.removeAll.rail",
  air: "graph:links.removeAll.air",
}
const MODE: ModeKeys = {
  rail: "graph:links.mode.rail",
  air: "graph:links.mode.air",
  river: "graph:links.mode.river",
  ferry: "graph:links.mode.ferry",
  winter_road: "graph:links.mode.winter_road",
  ice_crossing: "graph:links.mode.ice_crossing",
  pontoon_bridge: "graph:links.mode.pontoon_bridge",
}

export type LinkNames = ReadonlyMap<string, string>

export interface LinkText {
  readonly key: MessageKey
  readonly values: Readonly<Record<string, string | number>>
}

export function linkModeKey(mode: string): MessageKey | null {
  return MODE[mode] ?? null
}

export function linkChangeText(change: LinkChange, names: LinkNames = new Map()): LinkText {
  const source = names.get(change.source) ?? change.source
  const target = names.get(change.target) ?? change.target
  const values = { source, target, mode: change.mode, hours: change.hours ?? 0 }
  if (change.action === "add") return { key: ADD[change.mode] ?? "graph:links.add.other", values }
  if (change.target === "*")
    return { key: REMOVE_ALL[change.mode] ?? "graph:links.removeAll.other", values }
  return { key: REMOVE[change.mode] ?? "graph:links.remove.other", values }
}
