import type { NormativeMapLayer } from "@/shared/api/normative-map"
import type { components } from "@/shared/api/schema.gen"

export function municipalAccessLayer(
  data: components["schemas"]["MunicipalAccessResponse"] | undefined,
  onPoint: (id: string) => void,
  fallback?: NormativeMapLayer,
): NormativeMapLayer | undefined {
  if (!data) return fallback
  return {
    unit: data.unit === "metres" ? "metres" : "minutes",
    display: "status",
    rows: data.points.map(({ row, deficit }) => ({
      ...row,
      state: row.state === "unreachable" ? "unreachable" : deficit ? "exceeded" : row.state,
    })),
    facilities: [
      ...new Map(
        data.points.flatMap(({ facility }) => (facility ? [[facility.id, facility] as const] : [])),
      ).values(),
    ],
    onPoint,
  }
}
