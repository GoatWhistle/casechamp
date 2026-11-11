import { type UseQueryResult, useQueries, useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"
import type { RoadJob } from "@/shared/api/road-graph"

const FINISHED = new Set(["completed", "cancelled", "failed"])
const POLL_MS = 1500

export function useRoadJobs(ids: readonly string[]): UseQueryResult<RoadJob>[] {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: ["road-scenario", id],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        unwrap(
          api.GET("/api/v1/road-scenarios/{job_id}", { signal, params: { path: { job_id: id } } }),
        ),
      refetchInterval: (query: { state: { data: RoadJob | undefined } }) =>
        FINISHED.has(query.state.data?.status ?? "") ? false : POLL_MS,
    })),
  })
}

export function usePlaceNames(ids: readonly string[]): ReadonlyMap<string, string> {
  const sorted = [...new Set(ids)].sort()
  const query = useQuery({
    queryKey: ["road-graph-places", sorted],
    enabled: sorted.length > 0,
    staleTime: Number.POSITIVE_INFINITY,
    queryFn: ({ signal }) =>
      unwrap(api.GET("/api/v1/road-graph/places", { signal, params: { query: { ids: sorted } } })),
  })
  return new Map((query.data ?? []).map((place) => [place.point_id, place.name]))
}
