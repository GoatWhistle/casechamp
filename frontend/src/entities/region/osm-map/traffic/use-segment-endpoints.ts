import { type Map as LibreMap, Marker } from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import type { TrafficRoad } from "@/shared/api/traffic"
import { useTranslation } from "@/shared/i18n"
import styles from "./use-segment-endpoints.module.css"

export function useSegmentEndpoints(
  engine: RefObject<LibreMap | null>,
  ready: boolean,
  road: TrafficRoad | null,
) {
  const { t } = useTranslation()
  useEffect(() => {
    const map = engine.current
    if (!map || !ready || road?.edge_index == null) return
    const points = [road.coordinates[0], road.coordinates.at(-1)]
    const markers = points.flatMap((point, index) => {
      if (point?.[0] == null || point[1] == null) return []
      const element = document.createElement("span")
      element.className = styles.endpoint ?? ""
      element.textContent = t(
        index === 0 ? "map:municipalTraffic.endpointA" : "map:municipalTraffic.endpointB",
      )
      element.setAttribute("role", "img")
      element.setAttribute("aria-label", element.textContent)
      return [new Marker({ element }).setLngLat([point[0], point[1]]).addTo(map)]
    })
    return () => {
      for (const marker of markers) marker.remove()
    }
  }, [engine, ready, road, t])
}
