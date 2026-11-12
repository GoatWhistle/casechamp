import type { Assessment, Facility } from "@/entities/normative"

export function normativeScope(
  selectedId: string | null,
  _mode: string | null,
  result: Assessment | null | undefined,
  territory: string | undefined,
  regions: readonly { readonly id: string; readonly name: string }[] | undefined,
  facilities: Facility[] | undefined,
) {
  const options = regions ?? []
  const region = options.find((row) => row.name === (result?.region ?? territory))
  const selection = selectedId
  const visible = selectedId !== null && selectedId === region?.id
  return {
    selection,
    regionId: selection ?? "",
    regionName: options.find((row) => row.id === selection)?.name ?? null,
    result: visible ? result : null,
    facilities: visible ? facilities : undefined,
    options,
  }
}
