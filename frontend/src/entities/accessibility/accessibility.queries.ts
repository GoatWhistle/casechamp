import { useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type ComparisonData = components["schemas"]["AccessibilityComparison"]
export type ComparisonRow = components["schemas"]["AccessibilityRow"]
export type HalfLife = "2" | "4" | "8"

export function useAccessibility(regionId: string, halfLife: HalfLife) {
  return useQuery({
    queryKey: ["accessibility", regionId, halfLife],
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}/accessibility", {
          params: { path: { region_id: regionId }, query: { half_life: Number(halfLife) } },
          signal,
        }),
      ),
    enabled: regionId.length > 0,
  })
}
