import { useCallback, useMemo, useState } from "react"
import { useRegionLinks } from "@/entities/link"
import {
  useLatestNormativeAssessment,
  useNormativeCriteria,
  useNormativeFacilities,
  useRegionalIndexMap,
} from "@/entities/normative"
import {
  buildTransitCollection,
  type Season,
  useAirports,
  useGeoBoundaries,
  useOverview,
  useRegions,
} from "@/entities/region"
import type { NormativeDisplay, NormativeRouteStage } from "@/shared/api/normative-map"
import { type MetricKey, metricValue, normativeId } from "./metric"
import { buildScale, coverageScale } from "./scale"

export function useMapData(metric: MetricKey, season: Season, selectedId: string | null) {
  const geo = useGeoBoundaries()
  const regions = useRegions(season)
  const overview = useOverview()
  const criterionId = normativeId(metric)
  const [display, onDisplay] = useState<NormativeDisplay>("index")
  const [stage, onStage] = useState<NormativeRouteStage>("scenario")
  const indexMap = useRegionalIndexMap(criterionId ?? "", stage)
  const indexById = useMemo(
    () => new Map((indexMap.data ?? []).map((row) => [row.region_id, row.value_min])),
    [indexMap.data],
  )
  const normativeCriteria = useNormativeCriteria(Boolean(criterionId))
  const normativeTerritory = normativeCriteria.data?.find(
    (row) => row.id === criterionId,
  )?.territory

  const pilotId = geo.data?.regions.find((row) => row.name === normativeTerritory)?.id
  const pilotEnabled = selectedId === pilotId && display === "status"
  const normative = useLatestNormativeAssessment(criterionId ?? "", pilotEnabled)
  const normativeFacilities = useNormativeFacilities(criterionId ?? "", pilotEnabled)

  const byId = useMemo(() => new Map((regions.data ?? []).map((r) => [r.id, r])), [regions.data])
  const valueAt = useCallback(
    (id: string) => {
      const region = byId.get(id)
      if (criterionId && display === "index") return indexById.get(id) ?? null
      if (criterionId)
        return normative.data &&
          normative.data.scenario.unknown < normative.data.scenario.population &&
          normative.data.region === region?.name
          ? normative.data.scenario.lower_percent
          : null
      return region ? metricValue(region, metric) : null
    },
    [byId, metric, criterionId, normative.data, display, indexById],
  )
  const scale = useMemo(
    () =>
      criterionId && display === "index"
        ? coverageScale()
        : criterionId &&
            normative.data?.scenario.lower_percent != null &&
            normative.data.scenario.unknown < normative.data.scenario.population
          ? coverageScale()
          : buildScale((regions.data ?? []).map((region) => valueAt(region.id))),
    [regions.data, valueAt, criterionId, normative.data, display],
  )
  const missing = useMemo(
    () => (geo.data?.regions ?? []).some((region) => valueAt(region.id) === null),
    [geo.data, valueAt],
  )
  const failed = geo.isError || regions.isError || overview.isError
  const retry = () => {
    void geo.refetch()
    void regions.refetch()
    void overview.refetch()
  }

  return {
    geo,
    regions,
    overview,
    byId,
    valueAt,
    scale,
    missing,
    failed,
    retry,
    normative,
    normativeTerritory,
    normativeFacilities,
    normativeState: { display, onDisplay, stage, onStage },
  }
}

export function useSelectedTransit(selectedId: string | null, season: Season) {
  const links = useRegionLinks(selectedId, season)
  const airports = useAirports()
  const [showModels, setShowModels] = useState(false)
  const modelCount = (links.data ?? []).filter((link) => link.is_model).length
  const transit = useMemo(
    () =>
      buildTransitCollection(
        (links.data ?? []).filter((link) => showModels || !link.is_model),
        selectedId,
        airports.data,
      ),
    [links.data, selectedId, showModels, airports.data],
  )
  return { links, airports, transit, modelCount, showModels, setShowModels }
}
