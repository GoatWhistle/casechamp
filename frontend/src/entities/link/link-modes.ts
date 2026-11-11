import type { Link, Mode } from "./link.queries"

export const MODE_ORDER: readonly Mode[] = [
  "rail",
  "bus",
  "air",
  "river",
  "winter_road",
  "ferry",
  "ice_crossing",
  "pontoon_bridge",
]

export interface ModeShare {
  readonly mode: Mode
  readonly count: number
  readonly model: number
}

export interface LinkTally {
  readonly shares: readonly ModeShare[]
  readonly total: number
  readonly model: number
  readonly unknownSeason: number
}

function byCount(rows: readonly ModeShare[]): ModeShare[] {
  return [...rows].sort((a, b) => b.count - a.count)
}

export function tallyLinks(links: readonly Link[]): LinkTally {
  const counts = new Map<Mode, { count: number; model: number }>()
  let model = 0
  let unknownSeason = 0
  for (const link of links) {
    const row = counts.get(link.mode) ?? { count: 0, model: 0 }
    row.count += 1
    if (link.is_model) {
      row.model += 1
      model += 1
    }
    if (link.season === null) unknownSeason += 1
    counts.set(link.mode, row)
  }
  const shares = MODE_ORDER.flatMap((mode) => {
    const row = counts.get(mode)
    return row === undefined ? [] : [{ mode, ...row }]
  })
  return { shares: byCount(shares), total: links.length, model, unknownSeason }
}

export function sharesOfTotals(totals: Readonly<Record<Mode, number>>): ModeShare[] {
  return byCount(
    MODE_ORDER.filter((mode) => totals[mode] > 0).map((mode) => ({
      mode,
      count: totals[mode],
      model: 0,
    })),
  )
}

export function groupByMode(links: readonly Link[]): ReadonlyMap<Mode, readonly Link[]> {
  const groups = new Map<Mode, Link[]>()
  for (const link of links) {
    const group = groups.get(link.mode)
    if (group === undefined) groups.set(link.mode, [link])
    else group.push(link)
  }
  return groups
}
