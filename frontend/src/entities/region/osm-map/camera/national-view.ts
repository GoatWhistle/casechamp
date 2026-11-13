import type { Map as LibreMap } from "maplibre-gl"
import type { LonLatBounds } from "../boundary-geojson"

export const HOME_PADDING = 24
export const MIN_MAP_ZOOM = 0

function corners(home: LonLatBounds): [[number, number], [number, number]] {
  return [
    [home[0], home[1]],
    [home[2], home[3]],
  ]
}

export function isNationalView(map: LibreMap, home: LonLatBounds): boolean {
  if (map.isMoving()) return false
  const camera = map.cameraForBounds(corners(home), { padding: HOME_PADDING })
  if (!camera?.center || camera.zoom === undefined) return false
  const target = camera.center
  const center = Array.isArray(target)
    ? { lng: target[0], lat: target[1] }
    : "lng" in target
      ? target
      : { lng: target.lon, lat: target.lat }
  const current = map.getCenter()
  const longitude = ((current.lng - center.lng + 540) % 360) - 180
  return (
    Math.abs(longitude) < 0.0001 &&
    Math.abs(current.lat - center.lat) < 0.0001 &&
    Math.abs(map.getZoom() - camera.zoom) < 0.001
  )
}

export function fitNationalView(map: LibreMap, home: LonLatBounds, duration: number) {
  map.fitBounds(corners(home), { padding: HOME_PADDING, duration, maxZoom: 18 })
}

export function resizeMapView(map: LibreMap, home: LonLatBounds, ready: boolean): boolean {
  const national = ready && isNationalView(map, home)
  map.resize()
  if (national) {
    map.setMinZoom(MIN_MAP_ZOOM)
    fitNationalView(map, home, 0)
  }
  map.redraw()
  return national
}

export function observeMapResize(
  map: LibreMap,
  element: HTMLElement,
  home: () => LonLatBounds,
  ready: { readonly current: boolean },
): ResizeObserver {
  let size = [element.clientWidth, element.clientHeight] as const
  const resize = new ResizeObserver(() => {
    const next = [element.clientWidth, element.clientHeight] as const
    const shift: [number, number] = [(next[0] - size[0]) / 2, (next[1] - size[1]) / 2]
    size = next
    const national = resizeMapView(map, home(), ready.current)
    if (!national && (shift[0] !== 0 || shift[1] !== 0)) map.panBy(shift, { animate: false })
  })
  resize.observe(element)
  return resize
}
