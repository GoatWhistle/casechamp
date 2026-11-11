import { type Map as LibreMap, LngLat, type LngLatBoundsLike, type MapOptions } from "maplibre-gl"
import type { ChatMapCommand } from "@/shared/api/chat-map"
import type { BoundaryAtlas, LonLatBounds } from "./boundary-geojson"
import { NO_REGION, SELECTED_LAYER } from "./osm-style"

const ROAM_BASE = 12
const ROAM_ZOOM = 3
const ROAM_MAX = 16
const POLE = 85
const TURN = 360
const HALF_TURN = 180

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

export interface ZoomLimits {
  min: number
  max: number
}

export function roamConstrain(home: LonLatBounds, limits: ZoomLimits) {
  return (lngLat: LngLat, requested: number) => {
    const zoom = clamp(requested, limits.min, limits.max)
    const margin = Math.min(ROAM_MAX, ROAM_BASE / 2 ** (zoom - ROAM_ZOOM))
    const middle = (home[0] + home[2]) / 2
    const nearest = lngLat.lng + TURN * Math.round((middle - lngLat.lng) / TURN)
    const lng = clamp(nearest, home[0] - margin, home[2] + margin)
    const lat = clamp(
      lngLat.lat,
      Math.max(-POLE, home[1] - margin),
      Math.min(POLE, home[3] + margin),
    )
    return { center: new LngLat(lng > HALF_TURN ? lng - TURN : lng, lat), zoom }
  }
}

export const FLAT_MAP = {
  maxPitch: 0,
  pitchWithRotate: false,
  dragRotate: false,
  touchPitch: false,
} satisfies Partial<MapOptions>

export function keepFlat(map: LibreMap): LibreMap {
  map.touchZoomRotate.disableRotation()
  map.keyboard.disableRotation()
  return map
}

export function corners(bounds: LonLatBounds): LngLatBoundsLike {
  return [
    [bounds[0], bounds[1]],
    [bounds[2], bounds[3]],
  ]
}

export function regionFrame(atlas: BoundaryAtlas, ids: readonly string[]): LonLatBounds | null {
  const features = ids.map((id) => atlas.featureOf.get(id))
  if (!features.length || features.some((feature) => !feature)) return null
  const bounds = features.flatMap((feature) => (feature ? [feature.bounds] : []))
  return [
    Math.min(...bounds.map((box) => box[0])),
    Math.min(...bounds.map((box) => box[1])),
    Math.max(...bounds.map((box) => box[2])),
    Math.max(...bounds.map((box) => box[3])),
  ]
}

export function focusRegions(
  map: LibreMap,
  atlas: BoundaryAtlas,
  ids: readonly string[],
  duration: number,
) {
  const frame = ids.length ? regionFrame(atlas, ids) : atlas.home
  if (!frame) return
  map.stop()
  const selected = ids.map((id) => atlas.featureOf.get(id)?.id ?? NO_REGION)
  map.setFilter(SELECTED_LAYER, ["in", ["id"], ["literal", selected]])
  map.getContainer().dataset.focusRegions = ids.join(",")
  map.fitBounds(corners(frame), {
    padding: ids.length ? { top: 96, right: 56, bottom: 144, left: 56 } : 24,
    maxZoom: ids.length ? 8.5 : 18,
    duration,
    curve: 1.25,
    essential: false,
    linear: false,
  })
}

export function focusIds(
  command: ChatMapCommand | null | undefined,
  selectedId: string | null,
): readonly string[] {
  if (command?.action === "focus") return command.region_ids
  if (command?.action === "reset" || !selectedId) return []
  return [selectedId]
}

export function settlementCenter(
  target: NonNullable<ChatMapCommand["settlement"]>,
): [number, number] {
  return [target.longitude < 0 ? target.longitude + 360 : target.longitude, target.latitude]
}

export function aimCamera(
  map: LibreMap,
  atlas: BoundaryAtlas,
  command: ChatMapCommand | null | undefined,
  selectedId: string | null,
  duration: number,
  zoomDuration: number,
) {
  if (command?.action === "focus_settlement" && command.settlement) {
    const target = command.settlement
    map.stop()
    map.setFilter(SELECTED_LAYER, [
      "in",
      ["id"],
      ["literal", [atlas.featureOf.get(target.region_id)?.id ?? NO_REGION]],
    ])
    map.getContainer().dataset.focusRegions = target.region_id
    map.easeTo({
      center: settlementCenter(target),
      zoom: 12,
      duration,
      easing: (value) => 1 - (1 - value) ** 3,
      essential: false,
    })
    return
  }
  if (command?.action === "zoom_in" || command?.action === "zoom_out") {
    map.stop()
    map.zoomTo(map.getZoom() + (command.action === "zoom_in" ? 1 : -1), {
      duration: zoomDuration,
    })
    return
  }
  focusRegions(map, atlas, focusIds(command, selectedId), duration)
}
