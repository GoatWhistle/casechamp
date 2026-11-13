import type { FeatureCollection, Geometry } from "geojson"
import type { GeoJSONSource, Map as LibreMap, MapLayerMouseEvent } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { StressImpact } from "@/shared/api/road-stress"
import { selectStressImpact, useStressView } from "@/shared/hooks/use-stress-view"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { useVisibleStressPoints } from "../stress-map/use-visible-stress-points"
import { fitPadding } from "./camera/fit-padding"

const SOURCE = "road-stress-view"
export function useStressLayer(engine: RefObject<LibreMap | null>, ready: boolean) {
  const view = useStressView()
  const visible = useVisibleStressPoints(engine, ready)
  const focus = useRef(0)
  const reduced = useReducedMotion()
  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    const points = stressPoints(view, visible.data ?? [])
    map.getContainer().dataset.stressJob = view.jobId ?? ""
    map.getContainer().dataset.stressPoints = String(points.size)
    map.getContainer().dataset.stressClosed = String(view.closed?.length ?? 0)
    const data = stressFeatures({ ...view, impacts: [...points.values()] })
    if (!map.getSource(SOURCE)) {
      const tokens = getComputedStyle(map.getContainer())
      map.addSource(SOURCE, { type: "geojson", data })
      map.addLayer({
        id: `${SOURCE}-closed`,
        source: SOURCE,
        type: "line",
        filter: ["==", ["get", "kind"], "closed"],
        paint: {
          "line-color": tokens.getPropertyValue("--status-danger").trim(),
          "line-width": 6,
          "line-dasharray": [1, 1],
        },
      })
      map.addLayer({
        id: `${SOURCE}-before`,
        source: SOURCE,
        type: "line",
        filter: ["==", ["get", "kind"], "before"],
        paint: {
          "line-color": tokens.getPropertyValue("--text-muted").trim(),
          "line-width": 4,
          "line-dasharray": [2, 2],
        },
      })
      map.addLayer({
        id: `${SOURCE}-after`,
        source: SOURCE,
        type: "line",
        filter: ["==", ["get", "kind"], "after"],
        paint: {
          "line-color": tokens.getPropertyValue("--action-primary").trim(),
          "line-width": 5,
        },
      })
      map.addLayer({
        id: `${SOURCE}-points`,
        source: SOURCE,
        type: "circle",
        filter: ["==", ["get", "kind"], "point"],
        paint: {
          "circle-radius": 6,
          "circle-color": [
            "case",
            ["get", "isolated"],
            tokens.getPropertyValue("--status-danger").trim(),
            tokens.getPropertyValue("--action-primary").trim(),
          ],
        },
      })
    } else (map.getSource(SOURCE) as GeoJSONSource).setData(data)
    if (view.focus !== focus.current) {
      focus.current = view.focus
      focusView(map, view, reduced)
    }
    const click = (event: MapLayerMouseEvent) => {
      const id = event.features?.[0]?.properties.pointId
      const point = points.get(String(id))
      if (point) selectStressImpact(point)
    }
    map.on("click", `${SOURCE}-points`, click)
    return () => {
      map.off("click", `${SOURCE}-points`, click)
    }
  }, [engine, ready, view, reduced, visible.data])
}

export function focusView(map: LibreMap, view: ReturnType<typeof useStressView>, reduced: boolean) {
  const coordinates = view.route?.after.coordinates.length
    ? view.route.after.coordinates
    : view.route?.before.coordinates.length
      ? view.route.before.coordinates
      : view.closed?.length
        ? view.closed.flat()
        : view.impacts.map((r) => [r.point.longitude, r.point.latitude])
  if (!coordinates.length && view.regions?.length) {
    map.fitBounds(
      [
        [19, 41],
        [191, 81],
      ],
      { padding: fitPadding(map, 80), duration: reduced ? 0 : motionMs("--dur-panel") },
    )
  }
  if (coordinates.length) {
    const xs = coordinates.map((p) => ((p[0] ?? 0) < 0 ? (p[0] ?? 0) + 360 : (p[0] ?? 0)))
    const ys = coordinates.map((p) => p[1] ?? 0)
    map.fitBounds(
      [
        [
          xs.reduce((a, b) => Math.min(a, b), Infinity),
          ys.reduce((a, b) => Math.min(a, b), Infinity),
        ],
        [
          xs.reduce((a, b) => Math.max(a, b), -Infinity),
          ys.reduce((a, b) => Math.max(a, b), -Infinity),
        ],
      ],
      {
        padding: fitPadding(map, routePadding(map)),
        maxZoom: 12,
        duration: reduced ? 0 : motionMs("--dur-panel"),
      },
    )
  }
}

function stressFeatures(view: ReturnType<typeof useStressView>): FeatureCollection<Geometry> {
  const data: FeatureCollection<Geometry> = { type: "FeatureCollection", features: [] }
  if (view.closed?.length)
    data.features.push({
      type: "Feature",
      properties: { kind: "closed" },
      geometry: { type: "MultiLineString", coordinates: view.closed },
    })
  for (const impact of view.impacts)
    data.features.push({
      type: "Feature",
      properties: {
        pointId: impact.point.id,
        kind: "point",
        isolated: impact.external_isolation,
        name: impact.point.name,
      },
      geometry: { type: "Point", coordinates: [impact.point.longitude, impact.point.latitude] },
    })
  if (view.route)
    for (const key of ["before", "after"] as const) {
      const route = view.route[key]
      if (route.coordinates.length > 1)
        data.features.push({
          type: "Feature",
          properties: { kind: key },
          geometry: { type: "LineString", coordinates: route.coordinates },
        })
    }

  return data
}

function routePadding(map: LibreMap) {
  const bounds = map.getContainer().getBoundingClientRect()
  const panel = document
    .querySelector<HTMLElement>("[data-map-panel]:not([hidden]):not([inert])")
    ?.getBoundingClientRect()
  const padding = { top: 80, right: 80, bottom: 80, left: 80 }
  if (!panel || panel.width > bounds.width * 0.7) return padding
  const leftSpace = Math.max(0, panel.left - bounds.left)
  const rightSpace = Math.max(0, bounds.right - panel.right)
  if (leftSpace > rightSpace) padding.right = bounds.width - leftSpace + 24
  else padding.left = bounds.width - rightSpace + 24
  return padding
}

export function stressPoints(
  view: ReturnType<typeof useStressView>,
  visible: readonly StressImpact[],
) {
  if (view.showPoints === false) return new Map<string, StressImpact>()
  return new Map([...visible, ...view.impacts].map((point) => [point.point.id, point]))
}
