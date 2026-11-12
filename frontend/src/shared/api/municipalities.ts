import type { FeatureCollection, MultiPolygon } from "geojson"
import type { components } from "./schema.gen"

export type MunicipalityCatalog = components["schemas"]["MunicipalityCollectionResponse"]
export type MunicipalityProperties = components["schemas"]["MunicipalityPropertiesResponse"]
export interface MunicipalityLayer {
  readonly collection: FeatureCollection<MultiPolygon, MunicipalityProperties>
  readonly selected: string | null
  readonly onSelect: (id: string) => void
}
