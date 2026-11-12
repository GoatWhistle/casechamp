import type { RoadChangeInput } from "@/shared/api/road-graph"
import type { RoadProfileState } from "./road-profile-editor"

export function profilePayload(value: RoadProfileState): Omit<RoadChangeInput, "way_id"> | null {
  if (value.action === "closure") return { closed: true }
  if (value.action === "opening") return { closed: false }
  const lanes = Number(value.lanes.replace(",", "."))
  if (!value.lanes.trim() || !Number.isInteger(lanes) || lanes < 1 || lanes > 32) return null
  return { closed: false, lanes_total: lanes }
}
