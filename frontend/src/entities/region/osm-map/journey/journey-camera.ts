import { type Map as LibreMap, LngLatBounds } from "maplibre-gl"
import type { components } from "@/shared/api/schema.gen"

export function focusJourney(map: LibreMap, target: components["schemas"]["TransitMapTarget"]) {
  if (!target.points.length) return
  const bounds = new LngLatBounds()
  for (const point of target.points) bounds.extend([point.longitude, point.latitude])
  map.stop()
  map.fitBounds(bounds, {
    padding: { top: 100, right: 100, bottom: 100, left: 460 },
    maxZoom: 14,
    duration: 0,
  })
}
