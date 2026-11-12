import type { MultiPolygon } from "geojson"
import type { GeoJSONSource, Map as LibreMap, MapLayerMouseEvent } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { MunicipalityLayer } from "@/shared/api/municipalities"
import { motionMs, useReducedMotion } from "@/shared/motion"
import { NORMATIVE_OVERLAY_LAYERS } from "../normative-layer/use-normative-layer"
import { CONTEXTUAL_WATER_LAYER, SELECTED_LAYER } from "../osm-style"
import { roadLayers } from "../road-parts"
import { AIRPORT_LAYER } from "../use-airport-layer"

export const MUNICIPAL_FILL = "municipality-fill"
const SOURCE = "municipalities"
const OUTLINE = "municipality-outline"
const SELECTED = "municipality-selected"
export const MUNICIPAL_MIN_ZOOM = 0

export function municipalityBounds(
  geometry: MultiPolygon,
): [[number, number], [number, number]] | null {
  const positions = geometry.coordinates.flat(2)
  if (!positions.length) return null
  let west = Infinity,
    south = Infinity,
    east = -Infinity,
    north = -Infinity
  for (const point of positions) {
    const [x, y] = point
    if (x === undefined || y === undefined || !Number.isFinite(x) || !Number.isFinite(y))
      return null
    west = Math.min(west, x)
    south = Math.min(south, y)
    east = Math.max(east, x)
    north = Math.max(north, y)
  }
  return [
    [west, south],
    [east, north],
  ]
}

export function useMunicipalityLayer(
  engine: RefObject<LibreMap | null>,
  layer: MunicipalityLayer | undefined,
  ready: boolean,
) {
  const current = useRef(layer)
  current.current = layer
  const reduced = useReducedMotion()
  const collection = layer?.collection
  const selected = layer?.selected
  useEffect(() => {
    const map = engine.current
    if (!ready || !map || !collection) return
    if (!map.getSource(SOURCE)) {
      const style = getComputedStyle(map.getContainer())
      map.addSource(SOURCE, { type: "geojson", data: collection })
      const before = map.getLayer(SELECTED_LAYER) ? SELECTED_LAYER : undefined
      map.addLayer(
        {
          id: MUNICIPAL_FILL,
          type: "fill",
          source: SOURCE,
          minzoom: MUNICIPAL_MIN_ZOOM,
          paint: {
            "fill-color": style.getPropertyValue("--action-primary").trim(),
            "fill-opacity": 0.02,
          },
        },
        before,
      )
      map.addLayer(
        {
          id: OUTLINE,
          type: "line",
          source: SOURCE,
          minzoom: MUNICIPAL_MIN_ZOOM,
          paint: {
            "line-color": style.getPropertyValue("--text-secondary").trim(),
            "line-width": 1,
            "line-dasharray": [3, 2],
          },
        },
        before,
      )
      map.addLayer(
        {
          id: SELECTED,
          type: "line",
          source: SOURCE,
          minzoom: MUNICIPAL_MIN_ZOOM,
          filter: ["==", ["get", "id"], ""],
          paint: {
            "line-color": style.getPropertyValue("--action-primary").trim(),
            "line-width": 3,
          },
        },
        before,
      )
    } else (map.getSource(SOURCE) as GeoJSONSource).setData(collection)
  }, [engine, ready, collection])
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getLayer(SELECTED)) return
    map.setFilter(SELECTED, ["==", ["get", "id"], selected ?? ""])
    const feature = collection?.features.find((row) => row.properties.id === selected)
    const bounds = feature ? municipalityBounds(feature.geometry) : null
    if (bounds)
      map.fitBounds(bounds, {
        padding: 60,
        maxZoom: 11,
        duration: reduced ? 0 : motionMs("--dur-map", map.getContainer()),
      })
  }, [engine, ready, selected, collection, reduced])
  useEffect(() => {
    const map = engine.current
    if (!ready || !map) return
    const click = (event: MapLayerMouseEvent) => {
      const layers = [
        ...roadLayers(map),
        ...NORMATIVE_OVERLAY_LAYERS,
        CONTEXTUAL_WATER_LAYER,
        AIRPORT_LAYER,
      ].filter((id) => map.getLayer(id))
      if (layers.length && map.queryRenderedFeatures(event.point, { layers }).length) return
      const id = event.features?.[0]?.properties?.id
      if (typeof id === "string") current.current?.onSelect(id)
    }
    map.on("click", MUNICIPAL_FILL, click)
    return () => {
      map.off("click", MUNICIPAL_FILL, click)
    }
  }, [engine, ready])
}
