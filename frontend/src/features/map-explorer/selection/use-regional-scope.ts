import {
  type Assessment,
  type Facility,
  useRegionalNormativeCatalog,
  useRegionalRunView,
} from "@/entities/normative"
import { normativeScope } from "./normative-scope"

export function useRegionalScope(
  regionId: string,
  criterionId: string,
  enabled: boolean,
  pilot: Assessment | null | undefined,
  facilities: Facility[] | undefined,
) {
  const measurement = useRegionalRunView(regionId, criterionId, enabled)
  const catalog = useRegionalNormativeCatalog(
    regionId,
    criterionId,
    enabled && measurement.data === null,
  )
  return { result: pilot ?? measurement.data, facilities: facilities ?? catalog.data?.facilities }
}

export function useNormativeMapScope(
  selectedId: string | null,
  mode: string | null,
  data: {
    readonly result: Assessment | null | undefined
    readonly qualified: boolean
    readonly physical: boolean
    readonly territory: string | undefined
    readonly regions: readonly { readonly id: string; readonly name: string }[] | undefined
    readonly facilities: Facility[] | undefined
  },
) {
  const scope = normativeScope(
    selectedId,
    mode,
    data.qualified ? data.result : null,
    data.territory,
    data.regions,
    data.qualified ? data.facilities : undefined,
  )
  const regional = useRegionalScope(
    scope.regionId,
    mode ?? "",
    (scope.regionName !== data.territory || !data.qualified) && data.physical,
    scope.result,
    scope.facilities,
  )
  return { ...scope, result: regional.result, facilities: regional.facilities }
}
