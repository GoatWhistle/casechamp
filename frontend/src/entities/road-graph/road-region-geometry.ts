import type { RoadFocus } from "@/shared/api/road-graph"

type Point = readonly [number, number]
type Edge = readonly [Point, Point]
const EPSILON = 1e-10
const ROWS = 64

function point(value: readonly number[]): Point | null {
  return value.length >= 2 && Number.isFinite(value[0]) && Number.isFinite(value[1])
    ? [value[0] ?? 0, value[1] ?? 0]
    : null
}
function orientation(a: Point, b: Point, c: Point) {
  return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
}
function onSegment(a: Point, b: Point, p: Point) {
  return (
    Math.abs(orientation(a, b, p)) <= EPSILON &&
    p[0] >= Math.min(a[0], b[0]) - EPSILON &&
    p[0] <= Math.max(a[0], b[0]) + EPSILON &&
    p[1] >= Math.min(a[1], b[1]) - EPSILON &&
    p[1] <= Math.max(a[1], b[1]) + EPSILON
  )
}
function crosses(a: Point, b: Point, c: Point, d: Point) {
  const abC = orientation(a, b, c),
    abD = orientation(a, b, d)
  const cdA = orientation(c, d, a),
    cdB = orientation(c, d, b)
  return (
    (abC * abD < 0 && cdA * cdB < 0) ||
    onSegment(a, b, c) ||
    onSegment(a, b, d) ||
    onSegment(c, d, a) ||
    onSegment(c, d, b)
  )
}
function regionEdges(focus: RoadFocus): Edge[] {
  return focus.polygons.flatMap((polygon) =>
    polygon.flatMap((ring) =>
      ring.flatMap((value, index): Edge[] => {
        const a = point(value),
          b = point(ring[(index + 1) % ring.length] ?? [])
        return a && b ? [[a, b]] : []
      }),
    ),
  )
}

class RegionIntersection {
  south = Infinity
  north = -Infinity
  middle = 0
  rows: Edge[][] = Array.from({ length: ROWS }, () => [])

  constructor(focus: RoadFocus) {
    const edges = regionEdges(focus)
    let west = Infinity,
      east = -Infinity
    for (const [a, b] of edges)
      for (const p of [a, b]) {
        this.south = Math.min(this.south, p[1])
        this.north = Math.max(this.north, p[1])
        west = Math.min(west, p[0])
        east = Math.max(east, p[0])
      }
    this.middle = (west + east) / 2
    for (const edge of edges)
      for (
        let row = this.rowOf(Math.min(edge[0][1], edge[1][1]));
        row <= this.rowOf(Math.max(edge[0][1], edge[1][1]));
        row++
      )
        this.rows[row]?.push(edge)
  }

  rowOf(latitude: number) {
    return Math.max(
      0,
      Math.min(
        ROWS - 1,
        Math.floor(((latitude - this.south) / Math.max(this.north - this.south, EPSILON)) * ROWS),
      ),
    )
  }

  inside(p: Point) {
    if (p[1] < this.south || p[1] > this.north) return false
    let contained = false
    for (const [a, b] of this.rows[this.rowOf(p[1])] ?? []) {
      if (onSegment(a, b, p)) return true
      if (
        a[1] > p[1] !== b[1] > p[1] &&
        p[0] < ((b[0] - a[0]) * (p[1] - a[1])) / (b[1] - a[1]) + a[0]
      )
        contained = !contained
    }
    return contained
  }

  segment(a: Point, b: Point) {
    if (Math.max(a[1], b[1]) < this.south || Math.min(a[1], b[1]) > this.north) return false
    const candidates = new Set<Edge>()
    for (let row = this.rowOf(Math.min(a[1], b[1])); row <= this.rowOf(Math.max(a[1], b[1])); row++)
      for (const edge of this.rows[row] ?? []) candidates.add(edge)
    return [...candidates].some(([c, d]) => crosses(a, b, c, d))
  }

  intersects(coordinates: readonly number[][]) {
    const positions = coordinates.flatMap((value): Point[] => {
      const p = point(value)
      return p ? [[p[0] + 360 * Math.round((this.middle - p[0]) / 360), p[1]]] : []
    })
    if (positions.length !== coordinates.length) return false
    if (positions.some((p) => this.inside(p))) return true
    return positions.slice(1).some((b, index) => {
      const a = positions[index]
      return a ? this.segment(a, b) : false
    })
  }
}

export function prepareRegionIntersection(focus: RoadFocus) {
  const region = new RegionIntersection(focus)
  return (coordinates: readonly number[][]) => region.intersects(coordinates)
}
