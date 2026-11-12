import type { Map as LibreMap } from "maplibre-gl"
import type { BoundaryAtlas } from "../boundary-geojson"
import { REGIONS_SOURCE } from "../osm-style"

export function revealSelectedRegions(map: LibreMap, atlas: BoundaryAtlas, ids: readonly string[]) {
  const selected = new Set(ids)
  for (const [id, feature] of atlas.featureOf)
    map.setFeatureState({ source: REGIONS_SOURCE, id: feature.id }, { selected: selected.has(id) })
}
