import type { Map as LibreMap } from "maplibre-gl"
import { type RefObject, useMemo } from "react"
import type { LonLatBounds } from "../boundary-geojson"
import { corners } from "../map-camera"

export interface MapControls {
  readonly zoomIn: (instant?: boolean) => void
  readonly zoomOut: (instant?: boolean) => void
  readonly reset: (instant?: boolean) => void
}

export function useMapControls(
  engine: RefObject<LibreMap | null>,
  home: LonLatBounds,
  duration: (instant?: boolean) => number,
): MapControls {
  return useMemo(
    () => ({
      zoomIn: (instant?: boolean) => engine.current?.zoomIn({ duration: duration(instant) }),
      zoomOut: (instant?: boolean) => engine.current?.zoomOut({ duration: duration(instant) }),
      reset: (instant?: boolean) =>
        engine.current?.fitBounds(corners(home), { padding: 24, duration: duration(instant) }),
    }),
    [engine, home, duration],
  )
}
