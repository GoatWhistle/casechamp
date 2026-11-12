import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"
import type { Season } from "./region.queries"

function loadIndices(
  regionId: string,
  municipalityId: string,
  season: Season,
  signal: AbortSignal,
) {
  return unwrap(
    api.GET("/api/v1/regions/{region_id}/municipalities/{municipality_id}/indices", {
      params: {
        path: { region_id: regionId, municipality_id: municipalityId },
        query: { season: season === "all" ? "road" : season },
      },
      signal,
    }),
  )
}

export function useMunicipalityIndices(regionId: string, municipalityId: string, season: Season) {
  return useQuery<Awaited<ReturnType<typeof loadIndices>>>({
    queryKey: ["municipal-indices", regionId, municipalityId, season],
    queryFn: ({ signal }) => loadIndices(regionId, municipalityId, season, signal),
    enabled: regionId !== "" && municipalityId !== "",
    staleTime: 300_000,
    retry: false,
    refetchInterval: (query) =>
      query.state.data?.normative.some((row) => String(row.status) === "pending") ? 2000 : false,
  })
}
