import type { FeatureCollection, MultiPolygon } from "geojson"
import { useMemo, useState } from "react"
import {
  municipalAccessLayer,
  type Season,
  useMunicipalAccess,
  useMunicipalities,
} from "@/entities/region"
import type { MunicipalityLayer, MunicipalityProperties } from "@/shared/api/municipalities"
import type { NormativeMapLayer } from "@/shared/api/normative-map"
import {
  clearMunicipalAccess,
  selectMunicipalAccessPoint,
  useMunicipalAccessView,
} from "@/shared/hooks/use-municipal-access-view"
import { MunicipalOverview } from "./municipal-overview"
import { MunicipalityControl } from "./municipality-control"
import { MunicipalityIndexCard } from "./municipality-index-card"

export function useMunicipalitySelection(
  regionId: string | null,
  season: Season,
  ready: boolean,
  fallback?: NormativeMapLayer,
) {
  const query = useMunicipalities(regionId)
  const accessView = useMunicipalAccessView()
  const target = accessView.target?.region_id === regionId ? accessView.target : null
  const access = useMunicipalAccess(target)
  const [selection, setSelection] = useState<{ region: string | null; id: string } | null>(null)
  const [dismissedRegion, setDismissedRegion] = useState<string | null>(null)
  const overviewVisible = regionId !== null && dismissedRegion !== regionId
  const selected =
    target?.municipality_id ?? (selection && selection.region === regionId ? selection.id : null)
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
  const onSelect = (id: string) => {
    clearMunicipalAccess()
    setSelection({ region: regionId, id })
  }
  const current = query.data?.features.find((feature) => feature.properties.id === selected)
  const layer: MunicipalityLayer = { collection, selected, onSelect }
  const mapLayer = useMemo(
    () => municipalAccessLayer(access.data, selectMunicipalAccessPoint, fallback),
    [access.data, fallback],
  )
  return {
    layer,
    mapLayer,
    showLegend: ready && !(regionId && selected && current) && !overviewVisible,
    panel:
      regionId && selected && current ? (
        <MunicipalityIndexCard
          key={`${regionId}:${selected}:${target?.criterion_id ?? ""}:${target?.threshold ?? ""}`}
          regionId={regionId}
          municipalityId={selected}
          name={current.properties.name}
          season={season}
          onClear={() => {
            clearMunicipalAccess()
            setSelection(null)
          }}
        />
      ) : regionId && overviewVisible ? (
        <MunicipalOverview
          season={OVERVIEW_SEASONS[season]}
          regionId={regionId}
          onSelect={onSelect}
          onClear={() => setDismissedRegion(regionId)}
        />
      ) : null,
    control: regionId ? (
      <MunicipalityControl query={query} selected={selected} onSelect={onSelect} />
    ) : null,
  }
}

const OVERVIEW_SEASONS = { all: "road", summer: "summer", winter: "winter" } as const
