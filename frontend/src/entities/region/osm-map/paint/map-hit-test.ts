import type { Map as LibreMap, PointLike } from "maplibre-gl"
import { MUNICIPAL_FILL } from "../municipalities/use-municipality-layer"
import { NORMATIVE_OVERLAY_LAYERS } from "../normative-layer/use-normative-layer"
import { CONTEXTUAL_WATER_LAYER } from "../osm-style"
import { roadLayers } from "../road-parts"
import { AIRPORT_LAYER } from "../use-airport-layer"

export function blocksRegionSelection(map: LibreMap, point: PointLike): boolean {
  const layers = [
    ...NORMATIVE_OVERLAY_LAYERS,
    MUNICIPAL_FILL,
    CONTEXTUAL_WATER_LAYER,
    AIRPORT_LAYER,
    ...roadLayers(map),
  ].filter((id) => map.getLayer(id))
  return layers.length > 0 && map.queryRenderedFeatures(point, { layers }).length > 0
}
