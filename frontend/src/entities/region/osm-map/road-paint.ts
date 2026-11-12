import type {
  DataDrivenPropertyValueSpecification,
  ExpressionSpecification,
  FilterSpecification,
  LineLayerSpecification,
} from "maplibre-gl"

type Rank = readonly [major: number, primary: number, secondary: number, minor: number]

const ZOOMS = [4, 8, 12] as const

const WIDTH: readonly Rank[] = [
  [1.2, 0.85, 0.6, 0.45],
  [2.1, 1.5, 1, 0.7],
  [3.4, 2.6, 1.9, 1.4],
]

const OPACITY: readonly Rank[] = [
  [0.95, 0.8, 0.62, 0.5],
  [0.95, 0.82, 0.62, 0.48],
  [1, 0.9, 0.75, 0.6],
]

const SELECTED_WIDTH = [4, 5, 6] as const

function byRank(rank: Rank): ExpressionSpecification {
  return [
    "match",
    ["get", "highway"],
    ["motorway", "trunk"],
    rank[0],
    ["primary", "motorway_link", "trunk_link"],
    rank[1],
    ["secondary", "primary_link"],
    rank[2],
    rank[3],
  ]
}

function picked(ids: readonly number[]): ExpressionSpecification {
  return ["in", ["get", "way_id"], ["literal", ids]]
}

function byZoom(stop: (index: number) => ExpressionSpecification | number) {
  return [
    "interpolate",
    ["exponential", 1.5],
    ["zoom"],
    ...ZOOMS.flatMap((zoom, index) => [zoom, stop(index)]),
  ] as DataDrivenPropertyValueSpecification<number>
}

export function roadWidth(ids: readonly number[]) {
  return byZoom((index) => [
    "case",
    picked(ids),
    SELECTED_WIDTH[index] ?? 5,
    byRank(WIDTH[index] ?? WIDTH[0] ?? [1, 1, 1, 1]),
  ])
}

export function roadOpacity(ids: readonly number[]) {
  return byZoom((index) => [
    "case",
    picked(ids),
    1,
    byRank(OPACITY[index] ?? OPACITY[0] ?? [1, 1, 1, 1]),
  ])
}

export const ROAD_LAYOUT = {
  "line-cap": "round",
  "line-join": "round",
  "line-sort-key": byRank([3, 2, 1, 0]),
} satisfies LineLayerSpecification["layout"]

export function roadVisibility(ids: readonly number[]): FilterSpecification {
  return [
    "any",
    ["boolean", ["get", "focus_connected"], false],
    picked(ids),
    [
      "in",
      ["get", "highway"],
      ["literal", ["motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"]],
    ],
    [">=", ["zoom"], 9],
  ]
}
