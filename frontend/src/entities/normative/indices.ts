import { useQuery } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type RegionalIndex = components["schemas"]["RegionalIndexResponse"]

export function useRegionalIndex(regionId: string, criterionId: string, runId?: string) {
  return useQuery({
    queryKey: ["normative", "index", regionId, criterionId, runId],
    refetchInterval: 30_000,
    enabled: regionId !== "" && criterionId !== "",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regions/{region_id}/indices/{criterion_id}", {
          params: { path: { region_id: regionId, criterion_id: criterionId } },
          signal,
        }),
      ),
  })
}

export type IndexMapRegion = components["schemas"]["IndexMapRegionResponse"]

export function useRegionalIndexMap(
  criterionId: string,
  stage: "baseline" | "scenario" = "scenario",
) {
  return useQuery({
    queryKey: ["normative", "index-map", criterionId, stage],
    enabled: criterionId !== "",
    refetchInterval: 30_000,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/indices/{criterion_id}/regions", {
          params: { path: { criterion_id: criterionId }, query: { stage } },
          signal,
        }),
      ),
  })
}
