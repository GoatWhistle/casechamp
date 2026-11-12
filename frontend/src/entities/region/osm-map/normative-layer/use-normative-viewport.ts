import type { Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import type { RegionalViewport } from "@/shared/api/normative-map"

export function useNormativeViewport(
  engine: RefObject<LibreMap | null>,
  onViewport: ((viewport: RegionalViewport) => void) | undefined,
  ready: boolean,
) {
  useEffect(() => {
    const map = engine.current
    if (!map || !ready || !onViewport) return
    const report = () => {
      const bounds = map.getBounds()
      onViewport(
        normalizedViewport(
          bounds.getWest(),
          bounds.getSouth(),
          bounds.getEast(),
          bounds.getNorth(),
          map.getZoom(),
        ),
      )
    }
    report()
    map.on("moveend", report)
    return () => {
      map.off("moveend", report)
    }
  }, [engine, onViewport, ready])
}

export function normalizedViewport(
  west: number,
  south: number,
  east: number,
  north: number,
  zoom: number,
): RegionalViewport {
  const wrap = (value: number) => ((((value + 180) % 360) + 360) % 360) - 180
  return {
    west: east - west >= 360 ? -180 : wrap(west),
    east: east - west >= 360 ? 180 : wrap(east),
    south: Math.max(-90, south),
    north: Math.min(90, north),
    zoom: Math.min(20, Math.max(0, Math.floor(zoom))),
  }
}
