import type { components } from "./schema.gen"

export type ChatMapCommand = components["schemas"]["ChatMapCommand"]
export type MapCommandHandler = (command: ChatMapCommand) => void

export function isChatMapCommand(value: unknown): value is ChatMapCommand {
  if (
    typeof value !== "object" ||
    value === null ||
    !("action" in value) ||
    !("region_ids" in value)
  )
    return false
  if (
    !["focus", "focus_settlement", "focus_road", "reset", "zoom_in", "zoom_out"].includes(
      String(value.action),
    )
  )
    return false
  if (
    !Array.isArray(value.region_ids) ||
    !value.region_ids.every((id: unknown) => typeof id === "string" && /^\d{8}$/.test(id))
  )
    return false
  if (value.action === "focus_road")
    return value.region_ids.length === 0 && "road" in value && isRoadTarget(value.road)
  if (value.action === "focus_settlement") {
    if (!("settlement" in value) || typeof value.settlement !== "object" || !value.settlement)
      return false
    const target = value.settlement
    return (
      "id" in target &&
      typeof target.id === "string" &&
      target.id.length > 0 &&
      "name" in target &&
      typeof target.name === "string" &&
      target.name.length > 0 &&
      "region_id" in target &&
      typeof target.region_id === "string" &&
      value.region_ids.length === 1 &&
      value.region_ids[0] === target.region_id &&
      "longitude" in target &&
      typeof target.longitude === "number" &&
      Number.isFinite(target.longitude) &&
      "latitude" in target &&
      typeof target.latitude === "number" &&
      Number.isFinite(target.latitude) &&
      target.longitude >= -180 &&
      target.longitude <= 180 &&
      target.latitude >= -85 &&
      target.latitude <= 85
    )
  }
  return value.action === "focus"
    ? value.region_ids.length > 0 && value.region_ids.length <= 30
    : value.region_ids.length === 0
}

function isRoadTarget(value: unknown): boolean {
  if (typeof value !== "object" || !value) return false
  return (
    "names" in value &&
    Array.isArray(value.names) &&
    value.names.every((name: unknown) => typeof name === "string") &&
    "length_km" in value &&
    typeof value.length_km === "number" &&
    Number.isFinite(value.length_km) &&
    value.length_km >= 0 &&
    "lines" in value &&
    Array.isArray(value.lines) &&
    value.lines.length > 0 &&
    value.lines.every(
      (line: unknown) =>
        Array.isArray(line) &&
        line.length >= 2 &&
        line.every(
          (point: unknown) =>
            Array.isArray(point) &&
            point.length === 2 &&
            typeof point[0] === "number" &&
            Number.isFinite(point[0]) &&
            Math.abs(point[0]) <= 180 &&
            typeof point[1] === "number" &&
            Number.isFinite(point[1]) &&
            Math.abs(point[1]) <= 85,
        ),
    )
  )
}
