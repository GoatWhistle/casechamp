import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"

export function useMunicipalities(regionId: string | null) {
  return useQuery({
    queryKey: ["geo", "municipalities", regionId],
    enabled: Boolean(regionId),
    staleTime: Number.POSITIVE_INFINITY,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/regions/{region_id}/municipalities", {
          params: { path: { region_id: regionId ?? "" } },
          signal,
        }),
      ),
  })
}
