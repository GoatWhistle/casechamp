import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"

export function useMunicipalOverview(
  regionId: string,
  criterionId = "",
  season: "road" | "summer" | "winter" = "road",
) {
  return useQuery({
    queryKey: ["municipal-overview", regionId, criterionId, season],
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}/municipalities-overview", {
          params: {
            path: { region_id: regionId },
            query: {
              ...(criterionId ? { criterion_id: criterionId } : {}),
              season,
            },
          },
          signal,
        }),
      ),
    enabled: regionId !== "",
    staleTime: 300_000,
    retry: false,
  })
}
