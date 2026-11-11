import type { FeatureCollection, Point } from "geojson"
import { type GeoJSONSource, type Map as LibreMap, Popup } from "maplibre-gl"
import { type RefObject, useEffect, useRef } from "react"
import type { ChatMapCommand } from "@/shared/api/chat-map"
import { settlementCenter } from "./map-camera"
import styles from "./osm-map.module.css"

const SOURCE = "focused-settlement"

export function useSettlementFocus(
  engine: RefObject<LibreMap | null>,
  command: ChatMapCommand | null | undefined,
  ready: boolean,
) {
  const label = useRef<Popup | null>(null)
  useEffect(() => {
    const map = engine.current
    if (!ready || !map || command?.action === "zoom_in" || command?.action === "zoom_out") return
    label.current?.remove()
    label.current = null
    const target = command?.action === "focus_settlement" ? command.settlement : null
    const data: FeatureCollection<Point> = {
      type: "FeatureCollection",
      features: target
        ? [
            {
              type: "Feature",
              properties: { name: target.name },
              geometry: { type: "Point", coordinates: settlementCenter(target) },
            },
          ]
        : [],
    }
    const source = map.getSource(SOURCE) as GeoJSONSource | undefined
    if (source) source.setData(data)
    else if (target) {
      const style = getComputedStyle(map.getContainer())
      map.addSource(SOURCE, { type: "geojson", data })
      map.addLayer({
        id: SOURCE,
        type: "circle",
        source: SOURCE,
        paint: {
          "circle-radius": 7,
          "circle-color": style.getPropertyValue("--action-primary").trim(),
          "circle-stroke-color": style.getPropertyValue("--surface-base").trim(),
          "circle-stroke-width": 3,
        },
      })
    }
    map.getContainer().dataset.focusSettlement = target?.id ?? ""
    if (target)
      label.current = new Popup({
        closeButton: false,
        closeOnClick: false,
        offset: 12,
        anchor: "bottom",
        className: styles.airportPopup ?? "",
      })
        .setLngLat(settlementCenter(target))
        .setText(target.name)
        .addTo(map)
  }, [engine, command, ready])

  useEffect(
    () => () => {
      label.current?.remove()
      label.current = null
    },
    [],
  )
}
