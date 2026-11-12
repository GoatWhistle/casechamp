import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"

function loadMunicipalities(regionId: string, signal: AbortSignal) {
  return unwrap(
    api.GET("/api/v1/regions/{region_id}/municipalities", {
      params: { path: { region_id: regionId } },
      signal,
    }),
  )
}

export function useMunicipalities(regionId: string | null) {
  return useQuery<Awaited<ReturnType<typeof loadMunicipalities>>>({
    queryKey: ["geo", "municipalities", regionId],
    enabled: Boolean(regionId),
    staleTime: (query) => (query.state.data?.features.length ? Number.POSITIVE_INFINITY : 30_000),
    refetchInterval: (query) =>
      query.state.data && query.state.data.features.length === 0 ? 30_000 : false,
    queryFn: ({ signal }) => loadMunicipalities(regionId ?? "", signal),
  })
}
