import { type Map as LibreMap, Marker } from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import { useTransitView } from "@/shared/hooks/use-transit-view"
import { useTranslation } from "@/shared/i18n"
import { focusJourney } from "./journey-camera"
import styles from "./use-journey-points.module.css"

export function useJourneyPoints(engine: RefObject<LibreMap | null>, ready: boolean) {
  const target = useTransitView()
  const { t } = useTranslation()
  useEffect(() => {
    const map = engine.current
    if (!map || !ready || !target) return
    const color =
      getComputedStyle(map.getContainer()).getPropertyValue("--text-danger").trim() ||
      getComputedStyle(map.getContainer()).getPropertyValue("--action-primary").trim()
    const markers = target.points.map((point) => {
      const marker = new Marker({ color }).setLngLat([point.longitude, point.latitude]).addTo(map)
      const element = marker.getElement()
      if (styles.marker) element.classList.add(styles.marker)
      element.setAttribute("role", "img")
      element.setAttribute("aria-label", `${t(`map:transit.${point.role}`)}: ${point.name}`)
      element.setAttribute("title", `${t(`map:transit.${point.role}`)}: ${point.name}`)
      return marker
    })
    focusJourney(map, target)
    map.getContainer().dataset.transitPoints = String(markers.length)
    return () => {
      for (const marker of markers) marker.remove()
      delete map.getContainer().dataset.transitPoints
    }
  }, [engine, ready, target, t])
}
