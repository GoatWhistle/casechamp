import type { FeatureCollection, Point } from "geojson"
import {
  type GeoJSONSource,
  type Map as LibreMap,
  type MapGeoJSONFeature,
  type MapLayerMouseEvent,
  Popup,
} from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { AirportCatalog } from "@/shared/api/airports"
import { useTranslation } from "@/shared/i18n"
import styles from "./osm-map.module.css"

export const AIRPORT_LAYER = "airport-points"
export const AIRPORT_MIN_ZOOM = 5

export function useAirportLayer(
  engine: RefObject<LibreMap | null>,
  catalog: AirportCatalog | undefined,
  ready: boolean,
) {
  const { t } = useTranslation()
  const hover = useRef<(feature: MapGeoJSONFeature | undefined) => void>(() => undefined)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map || !catalog) return
    const data: FeatureCollection<Point> = {
      type: "FeatureCollection",
      features: catalog.airports.map((airport) => ({
        type: "Feature",
        properties: {
          id: airport.id,
          name: airport.name,
          iata: airport.iata,
          scheduled: airport.scheduled,
        },
        geometry: { type: "Point", coordinates: [airport.longitude, airport.latitude] },
      })),
    }
    if (!map.getSource(AIRPORT_LAYER)) {
      const style = getComputedStyle(map.getContainer())
      map.addSource(AIRPORT_LAYER, { type: "geojson", data })
      map.addLayer({
        id: AIRPORT_LAYER,
        type: "circle",
        source: AIRPORT_LAYER,
        minzoom: AIRPORT_MIN_ZOOM,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 2.5, 6, 3.5, 10, 6],
          "circle-color": style.getPropertyValue("--mode-air").trim(),
          "circle-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.8, 7, 1],
          "circle-stroke-color": style.getPropertyValue("--surface-base").trim(),
          "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 3, 1, 8, 1.5],
          "circle-stroke-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.7, 7, 1],
        },
      })
    } else (map.getSource(AIRPORT_LAYER) as GeoJSONSource).setData(data)
    const popup = new Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: getComputedStyle(map.getContainer()).getPropertyValue("--legend-width").trim(),
      className: styles.airportPopup ?? "",
    })
    let hovered: string | null = null
    const show = (feature: MapGeoJSONFeature | undefined) => {
      if (feature?.geometry.type !== "Point") return
      const properties = feature.properties
      const x = feature.geometry.coordinates[0]
      const y = feature.geometry.coordinates[1]
      if (x === undefined || y === undefined) return
      popup
        .setLngLat([x, y])
        .setText(
          t("map:airports.detail", {
            name: properties.name,
            code: properties.iata || properties.id,
          }),
        )
        .addTo(map)
    }
    const hide = () => {
      popup.remove()
    }
    hover.current = (feature) => {
      if (map.getZoom() < AIRPORT_MIN_ZOOM) {
        hovered = null
        hide()
        return
      }
      const id = feature ? String(feature.properties.id) : null
      if (id === hovered) return
      hovered = id
      if (feature) show(feature)
      else hide()
    }
    const click = (event: MapLayerMouseEvent) => hover.current(event.features?.[0])
    const zoom = () => {
      if (map.getZoom() < AIRPORT_MIN_ZOOM) hover.current(undefined)
    }
    map.on("zoom", zoom)
    map.on("click", AIRPORT_LAYER, click)
    map.getContainer().dataset.airportCount = String(data.features.length)
    return () => {
      popup.remove()
      hover.current = () => undefined
      map.off("zoom", zoom)
      map.off("click", AIRPORT_LAYER, click)
    }
  }, [engine, catalog, ready, t])
  return hover
}
