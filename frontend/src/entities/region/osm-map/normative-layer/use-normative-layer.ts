import type { FeatureCollection, Point } from "geojson"
import {
  type GeoJSONSource,
  type Map as LibreMap,
  type MapLayerMouseEvent,
  Popup,
} from "maplibre-gl"
import { type RefObject, useEffect, useMemo } from "react"
import type { NormativeDisplay, NormativeMapLayer } from "@/shared/api/normative-map"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { useReducedMotion } from "@/shared/motion"
import { focusCluster } from "./normative-cluster-focus"
import { normativePointColor } from "./normative-point-color"
import { buildData } from "./normative-point-data"
import { ROUTE_LAYERS, useNormativeRouteLayer } from "./use-normative-route"
import { useNormativeViewport } from "./use-normative-viewport"

const SOURCE = "normative-access"
export const NORMATIVE_POINTS_LAYER = "normative-points"
export const NORMATIVE_FACILITIES_LAYER = "normative-facilities"
export const NORMATIVE_OVERLAY_LAYERS = [
  NORMATIVE_POINTS_LAYER,
  NORMATIVE_FACILITIES_LAYER,
  ...ROUTE_LAYERS,
]

export function useNormativeLayer(
  engine: RefObject<LibreMap | null>,
  layer: NormativeMapLayer | undefined,
  ready: boolean,
) {
  const reduced = useReducedMotion()
  useNormativeViewport(engine, layer?.onViewport, ready)
  useNormativeRouteLayer(
    engine,
    layer?.display === "index" ? undefined : layer?.route,
    ready,
    NORMATIVE_POINTS_LAYER,
  )
  const clusters = layer?.clusters
  const facilityClusters = layer?.facilityClusters
  const unit = layer?.unit
  const rows = layer?.rows
  const facilities = layer?.facilities
  const onPoint = layer?.onPoint
  const display = layer?.display
  const points = useMemo(
    () =>
      rows && facilities && onPoint
        ? { rows, facilities, onPoint, display, clusters, facilityClusters, unit }
        : undefined,
    [rows, facilities, onPoint, display, clusters, facilityClusters, unit],
  )
  const { t } = useTranslation()
  const f = useFormatters()
  useEffect(() => {
    const map = engine.current
    if (!map || !ready) return
    if (!points || display === "index") {
      removeSource(map)
      if (points) map.getContainer().dataset.normativeDisplay = "index"
      return
    }
    syncSource(map, buildData(points, t, f), display)
    for (const id of [NORMATIVE_POINTS_LAYER, NORMATIVE_FACILITIES_LAYER])
      map.setLayoutProperty(id, "visibility", "visible")
    const unbind = bindInteractions(map, points.onPoint, reduced)
    markPointCounts(map, points)
    return unbind
  }, [engine, points, display, ready, t, f, reduced])
}

function syncSource(map: LibreMap, data: FeatureCollection<Point>, display?: NormativeDisplay) {
  const style = getComputedStyle(map.getContainer())
  const color = (key: string) => style.getPropertyValue(key).trim()
  const paint = normativePointColor(data, display, color)
  if (map.getSource(SOURCE)) {
    ;(map.getSource(SOURCE) as GeoJSONSource).setData(data)
    map.setPaintProperty(NORMATIVE_POINTS_LAYER, "circle-color", paint)
  } else {
    map.addSource(SOURCE, { type: "geojson", data })
    map.addLayer({
      id: NORMATIVE_POINTS_LAYER,
      type: "circle",
      source: SOURCE,
      filter: ["==", ["get", "kind"], "origin"],
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["coalesce", ["get", "count"], 1],
          1,
          4,
          10,
          8,
          100,
          12,
          1000,
          18,
        ],
        "circle-color": paint,
        "circle-stroke-width": 1,
        "circle-stroke-color": color("--surface-raised"),
        "circle-opacity": 0.9,
      },
    })
    map.addLayer({
      id: NORMATIVE_FACILITIES_LAYER,
      type: "circle",
      source: SOURCE,
      filter: ["==", ["get", "kind"], "facility"],
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["coalesce", ["get", "count"], 1],
          1,
          6,
          10,
          10,
          100,
          16,
        ],
        "circle-color": color("--action-primary"),
        "circle-stroke-width": 2,
        "circle-stroke-color": color("--surface-raised"),
      },
    })
  }
}

function removeSource(map: LibreMap) {
  for (const id of [NORMATIVE_POINTS_LAYER, NORMATIVE_FACILITIES_LAYER]) {
    if (map.getLayer(id)) map.removeLayer(id)
  }
  if (map.getSource(SOURCE)) map.removeSource(SOURCE)
  delete map.getContainer().dataset.normativePoints
  delete map.getContainer().dataset.normativeDisplay
  delete map.getContainer().dataset.normativeFacilities
}

function bindInteractions(map: LibreMap, onPoint: (id: string) => void, reduced: boolean) {
  const popup = new Popup({ closeButton: false, closeOnClick: false, offset: 24 })
  const show = (event: MapLayerMouseEvent) => {
    const feature = event.features?.[0]
    if (feature?.geometry.type !== "Point") return
    const [x, y] = feature.geometry.coordinates
    if (x === undefined || y === undefined) return
    popup
      .setLngLat([x, y])
      .setText(String(feature.properties?.text ?? ""))
      .addTo(map)
  }
  const pick = (event: MapLayerMouseEvent) => {
    show(event)
    const feature = event.features?.[0]
    if (focusCluster(map, feature?.properties, reduced)) return
    if (feature?.properties?.kind === "origin") onPoint(String(feature.properties.id))
  }
  const hide = () => {
    popup.remove()
  }
  for (const id of [NORMATIVE_POINTS_LAYER, NORMATIVE_FACILITIES_LAYER]) {
    map.on("mouseenter", id, show)
    map.on("mouseleave", id, hide)
    map.on("click", id, pick)
  }
  return () => {
    popup.remove()
    for (const id of [NORMATIVE_POINTS_LAYER, NORMATIVE_FACILITIES_LAYER]) {
      map.off("mouseenter", id, show)
      map.off("mouseleave", id, hide)
      map.off("click", id, pick)
    }
  }
}

function markPointCounts(map: LibreMap, points: NormativeMapLayer) {
  map.getContainer().dataset.normativePoints = String(
    points.clusters
      ? points.clusters.reduce((sum, cell) => sum + cell.references, 0)
      : points.rows.length,
  )
  map.getContainer().dataset.normativeFacilities = String(
    points.facilityClusters
      ? points.facilityClusters.reduce((sum, cell) => sum + cell.facilities, 0)
      : points.facilities.filter((point) => point.latitude !== null && point.longitude !== null)
          .length,
  )
  map.getContainer().dataset.normativeDisplay = points.display ?? "status"
}
