import type { FeatureCollection, MultiPolygon } from "geojson"
import { useMemo, useState } from "react"
import { type Season, useMunicipalities } from "@/entities/region"
import type { MunicipalityLayer, MunicipalityProperties } from "@/shared/api/municipalities"
import { MunicipalityControl } from "./municipality-control"
import { MunicipalityIndexCard } from "./municipality-index-card"

export function useMunicipalitySelection(regionId: string | null, season: Season, ready: boolean) {
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
  const current = query.data?.features.find((feature) => feature.properties.id === selected)
  const layer: MunicipalityLayer = { collection, selected, onSelect }
  return {
    layer,
    showLegend: ready && !(regionId && selected && current),
    panel:
      regionId && selected && current ? (
        <MunicipalityIndexCard
          key={`${regionId}:${selected}`}
          regionId={regionId}
          municipalityId={selected}
          name={current.properties.name}
          season={season}
          onClear={() => setSelection(null)}
        />
      ) : null,
    control: regionId ? (
      <MunicipalityControl query={query} selected={selected} onSelect={onSelect} />
    ) : null,
  }
}
