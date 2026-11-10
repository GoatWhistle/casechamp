import type { RegionSummary } from "./region.queries"

export function modelRegionId(
  selectedId: string | null,
  regions: readonly RegionSummary[] | undefined,
): string | null {
  return selectedId !== null && regions?.some((region) => region.id === selectedId)
    ? selectedId
    : null
}

export function boundaryName(
  id: string | null,
  boundaries: readonly { readonly id: string; readonly name: string }[] | undefined,
): string | null {
  return boundaries?.find((region) => region.id === id)?.name ?? null
}
