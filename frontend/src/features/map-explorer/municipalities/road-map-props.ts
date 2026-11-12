import type { RoadGraphState } from "@/entities/road-graph"
import type { RoadLayerProps } from "@/shared/api/road-graph"

export function roadMapProps(roads: RoadGraphState): RoadLayerProps {
  return {
    view: roads.layerView,
    onRendering: roads.setRendering,
    addition: roads.addition,
    analysis: roads.analysisOverlay,
    corridor: roads.corridorOverlay,
    selected: roads.selected,
    onBounds: roads.onBounds,
    onRoad: roads.onRoad,
  }
}
