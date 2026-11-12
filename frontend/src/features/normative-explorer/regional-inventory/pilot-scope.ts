import type { Criterion, Facility } from "@/entities/normative"
import type { NormativeDisplay } from "@/shared/api/normative-map"

export function outsideRegion(
  regionName: string | null | undefined,
  criterion: Criterion | undefined,
) {
  return Boolean(regionName && criterion && criterion.territory !== regionName)
}

export function pilotScopeEnabled(
  regionName: string | null | undefined,
  criterion: Criterion | undefined,
  regionId: string | null | undefined,
) {
  return Boolean(regionId && criterion?.territory === regionName)
}

export function canCalculate(
  criterion: Criterion | undefined,
  facilities: readonly Facility[] | undefined,
) {
  return (
    (criterion?.mode === "car" ||
      criterion?.mode === "walk" ||
      criterion?.service === "library" ||
      criterion?.service === "fire") &&
    Boolean(facilities?.some((row) => row.latitude !== null && row.longitude !== null))
  )
}

export function showRegionalInventory(
  display: NormativeDisplay | undefined,
  regionName: string | null | undefined,
  criterion: Criterion | undefined,
) {
  return display !== "status" || outsideRegion(regionName, criterion)
}
