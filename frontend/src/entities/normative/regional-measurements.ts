import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type RegionalMeasurement = components["schemas"]["RegionalMeasurementResponse"]

export function useRegionalMeasurement(regionId: string, criterionId: string, enabled = true) {
  return useQuery({
    queryKey: ["normative", "regional-measurement", regionId, criterionId],
    enabled: enabled && regionId !== "" && criterionId !== "",
    staleTime: 60_000,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regions/{region_id}/measurements/{criterion_id}/latest", {
          params: { path: { region_id: regionId, criterion_id: criterionId } },
          signal,
        }),
      ),
  })
}

export function useCalculateRegionalMeasurement(
  regionId: string,
  criterionId: string,
  fireProfile?: components["schemas"]["FireProfileInput"] | null,
) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (closedWayIds: number[]) =>
      unwrap(
        api.POST("/api/v1/normative/regions/{region_id}/measurements/{criterion_id}/receipt", {
          params: { path: { region_id: regionId, criterion_id: criterionId } },
          body: { closed_way_ids: closedWayIds, fire_profile: fireProfile ?? null },
        }),
      ),
    onSuccess: async (result) => {
      await Promise.all([
        client.invalidateQueries({
          queryKey: ["normative", "regional-view", result.region_id, result.criterion_id],
        }),
        client.invalidateQueries({
          queryKey: ["normative", "index", result.region_id, result.criterion_id],
        }),
        client.invalidateQueries({ queryKey: ["normative", "index-map", result.criterion_id] }),
      ])
    },
  })
}
