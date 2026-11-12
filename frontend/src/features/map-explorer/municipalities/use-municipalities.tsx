import type { FeatureCollection, MultiPolygon } from "geojson"
import { useMemo, useState } from "react"
import { useMunicipalities } from "@/entities/region"
import type { MunicipalityLayer, MunicipalityProperties } from "@/shared/api/municipalities"
import { MunicipalityControl } from "./municipality-control"

export function useMunicipalitySelection(regionId: string | null) {
  const query = useMunicipalities(regionId)
  const [selection, setSelection] = useState<{ region: string | null; id: string } | null>(null)
  const selected = selection && selection.region === regionId ? selection.id : null
  const collection = useMemo<FeatureCollection<MultiPolygon, MunicipalityProperties>>(
    () => ({
      type: "FeatureCollection",
      features: (query.data?.features ?? []).map((feature) => ({
        type: "Feature",
        properties: feature.properties,
        geometry: { type: "MultiPolygon", coordinates: feature.geometry.coordinates },
      })),
    }),
    [query.data],
  )
  const onSelect = (id: string) => setSelection({ region: regionId, id })
  const layer: MunicipalityLayer = { collection, selected, onSelect }
  return {
    layer,
    control: regionId ? (
      <MunicipalityControl query={query} selected={selected} onSelect={onSelect} />
    ) : null,
  }
}
