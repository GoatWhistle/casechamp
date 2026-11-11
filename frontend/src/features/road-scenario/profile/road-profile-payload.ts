import type { RoadChangeInput } from "@/shared/api/road-graph"
import type { RoadProfileState } from "./road-profile-editor"

export function profilePayload(
  value: RoadProfileState,
): Omit<RoadChangeInput, "way_id" | "speed_factor"> | null {
  const lanes = value.lanes.trim() ? Number(value.lanes.replace(",", ".")) : null
  const speed = value.speed.trim() ? Number(value.speed.replace(",", ".")) : null
  if (lanes !== null && (!Number.isInteger(lanes) || lanes < 1 || lanes > 32)) return null
  if (speed !== null && (!Number.isFinite(speed) || speed <= 0 || speed > 200)) return null
  if (lanes === null && speed === null && !value.highway && !value.surface) return null
  return {
    ...(lanes === null ? {} : { lanes_total: lanes }),
    ...(speed === null ? {} : { speed_kmh: speed }),
    ...(value.highway ? { highway: value.highway } : {}),
    ...(value.surface ? { surface: value.surface } : {}),
  }
}

export function speedFactor(raw: string): number | null {
  const value = Number(raw.replace(",", "."))
  return raw.trim() && Number.isFinite(value) && value >= 0 && value <= 3 ? value : null
}
