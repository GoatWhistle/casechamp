import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"

export function useGraphLocations(query: string, regionId: string | null = null) {
  return useQuery({
    queryKey: ["graph-locations", query.trim(), regionId],
    enabled: query.trim().length >= 2,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-graph/locations", {
          signal,
          params: { query: { query: query.trim(), ...(regionId ? { region_id: regionId } : {}) } },
        }),
      ),
  })
}
