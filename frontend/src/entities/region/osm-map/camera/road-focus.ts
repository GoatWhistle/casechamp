import type { Feature, MultiLineString } from "geojson"
import type { GeoJSONSource, Map as LibreMap } from "maplibre-gl"
import type { ChatMapCommand } from "@/shared/api/chat-map"

const SOURCE = "focused-road"

export function updateRoadFocus(map: LibreMap, command: ChatMapCommand | null | undefined) {
  if (command?.action === "zoom_in" || command?.action === "zoom_out") return
  const road = command?.action === "focus_road" ? command.road : null
  if (!road) {
    if (map.getLayer(SOURCE)) map.removeLayer(SOURCE)
    if (map.getSource(SOURCE)) map.removeSource(SOURCE)
    delete map.getContainer().dataset.focusRoad
    return
  }
  const data: Feature<MultiLineString> = {
    type: "Feature",
    properties: {},
    geometry: { type: "MultiLineString", coordinates: road.lines },
  }
  const source = map.getSource(SOURCE) as GeoJSONSource | undefined
  if (source) source.setData(data)
  else {
    map.addSource(SOURCE, { type: "geojson", data })
    map.addLayer({
      id: SOURCE,
      source: SOURCE,
      type: "line",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": getComputedStyle(map.getContainer())
          .getPropertyValue("--agent-action")
          .trim(),
        "line-width": 6,
      },
    })
  }
  map.moveLayer(SOURCE)
  map.getContainer().dataset.focusRoad = road.names.join(", ")
}

export function focusRoad(map: LibreMap, lines: number[][][], duration: number) {
  let west = Infinity
  let south = Infinity
  let east = -Infinity
  let north = -Infinity
  for (const line of lines)
    for (const [longitude = 0, latitude = 0] of line) {
      const x = longitude < 0 ? longitude + 360 : longitude
      west = Math.min(west, x)
      east = Math.max(east, x)
      south = Math.min(south, latitude)
      north = Math.max(north, latitude)
    }
  if (!Number.isFinite(west)) return
  map.stop()
  map.fitBounds(
    [
      [west, south],
      [east, north],
    ],
    { padding: roadPadding(map), maxZoom: 16, duration, essential: false },
  )
}

function roadPadding(map: LibreMap) {
  const bounds = map.getContainer().getBoundingClientRect()
  const gap = Math.min(64, bounds.width / 8, bounds.height / 8)
  const padding = { top: gap, right: gap, bottom: gap, left: gap }
  const panel = document
    .querySelector<HTMLElement>("[data-map-panel]:not([hidden]):not([inert])")
    ?.getBoundingClientRect()
  if (!panel || panel.width > bounds.width * 0.7) return padding
  const left = Math.max(0, panel.left - bounds.left)
  const right = Math.max(0, bounds.right - panel.right)
  if (left > right) padding.right = bounds.width - left + gap
  else padding.left = bounds.width - right + gap
  return padding
}
