import type { FeatureCollection, LineString } from "geojson"
import type { components } from "@/shared/api"
import type { AirportCatalog } from "@/shared/api/airports"

type Link = components["schemas"]["LinkResponse"]
type Position = [number, number]

const ARC_BEND = 0.2
const ARC_STEPS = 48
type Endpoint = Link["from"]

function position(endpoint: Endpoint): [number, number] | null {
  const { lon, lat } = endpoint
  if (
    typeof lon !== "number" ||
    typeof lat !== "number" ||
    !Number.isFinite(lon) ||
    !Number.isFinite(lat) ||
    Math.abs(lon) > 180 ||
    Math.abs(lat) > 90
  )
    return null
  return [lon, lat]
}

export function buildTransitCollection(
  links: readonly Link[],
  regionId: string | null,
  catalog?: AirportCatalog,
) {
  const data: FeatureCollection<LineString> = { type: "FeatureCollection", features: [] }
  const seen = new Set<string>()
  const airports = new Map(catalog?.airports.map((airport) => [airport.id, airport]))
  const assigned = new Map(
    catalog?.assignments.map((assignment) => [
      assignment.point_id,
      airports.get(assignment.airport_id),
    ]),
  )
  let missing = 0
  let modeled = false
  for (const link of links) {
    if (!isTransit(link, regionId)) continue
    modeled ||= link.is_model === true
    const modelAir = link.mode === "air" && link.is_model
    const from = endpointPosition(link.from, link.mode === "air", modelAir, assigned)
    const to = endpointPosition(link.to, link.mode === "air", modelAir, assigned)
    if (!from || !to) {
      missing++
      continue
    }
    if (from[0] === to[0] && from[1] === to[1]) continue
    const key = `${link.mode}:${[from.join(","), to.join(",")].sort().join(";")}`
    if (seen.has(key)) continue
    seen.add(key)
    data.features.push(transitFeature(link.mode, from, to))
  }
  return { data, missing, modeled }
}

function transitFeature(mode: string, from: Position, to: Position) {
  const delta = to[0] - from[0]
  if (Math.abs(delta) > 180) to[0] -= Math.sign(delta) * 360
  return {
    type: "Feature" as const,
    properties: { mode },
    geometry: {
      type: "LineString" as const,
      coordinates: mode === "air" ? flightArc(from, to) : [from, to],
    },
  }
}

function endpointPosition(
  endpoint: Endpoint,
  air: boolean,
  modelAir: boolean,
  assigned: Map<string, AirportCatalog["airports"][number] | undefined>,
): [number, number] | null {
  if (!air) return position(endpoint)
  const airport = assigned.get(endpoint.id)
  return airport ? [airport.longitude, airport.latitude] : modelAir ? null : position(endpoint)
}

function isTransit(link: Link, regionId: string | null) {
  return link.region_id === regionId && (link.mode === "rail" || link.mode === "air")
}

export function flightArc(from: Position, to: Position): Position[] {
  const [x1, y1] = from
  const [x2, y2] = to
  const dx = x2 - x1
  const dy = y2 - y1
  const side = dx === 0 ? 1 : Math.sign(dx)
  const cx = (x1 + x2) / 2 - dy * ARC_BEND * side
  const cy = (y1 + y2) / 2 + Math.abs(dx) * ARC_BEND
  return Array.from({ length: ARC_STEPS + 1 }, (_, step) => {
    const t = step / ARC_STEPS
    const u = 1 - t
    return [u * u * x1 + 2 * u * t * cx + t * t * x2, u * u * y1 + 2 * u * t * cy + t * t * y2]
  })
}
