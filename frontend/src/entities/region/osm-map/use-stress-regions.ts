import type { Map as LibreMap, MapLayerMouseEvent } from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import { selectStressRegion, useStressView } from "@/shared/hooks/use-stress-view"
import { REGIONS_SOURCE } from "./osm-style"

export function useStressRegions(engine: RefObject<LibreMap | null>, ready: boolean) {
  const view = useStressView()
  useEffect(() => {
    const map = engine.current
    if (!ready || !map?.getSource(REGIONS_SOURCE)) return
    const layer = "road-stress-regions"
    if (!map.getLayer(layer)) {
      const style = getComputedStyle(map.getContainer())
      map.addLayer({
        id: layer,
        source: REGIONS_SOURCE,
        type: "fill",
        paint: {
          "fill-color": style.getPropertyValue("--action-primary").trim(),
          "fill-opacity": 0.25,
        },
      })
    }
    map.setFilter(layer, [
      "in",
      ["get", "name"],
      ["literal", (view.showPoints === false ? [] : (view.regions ?? [])).map((r) => r.name)],
    ])
    const click = (event: MapLayerMouseEvent) => {
      const name = event.features?.[0]?.properties.name
      if (typeof name === "string") selectStressRegion(name)
    }
    map.on("click", layer, click)
    return () => {
      map.off("click", layer, click)
    }
  }, [engine, ready, view])
}
