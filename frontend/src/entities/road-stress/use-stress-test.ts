import { useMutation, useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"

export function useStressTest(id: string | null, region: string, offset: number) {
  const job = useQuery({
    queryKey: ["road-stress", id],
    enabled: id !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}", {
          signal,
          params: { path: { job_id: id ?? "" } },
        }),
      ),
    refetchInterval: (query) =>
      ["completed", "failed", "cancelled"].includes(query.state.data?.status ?? "") ? false : 1500,
  })
  const parentId = job.data?.parent_id
  const summary = useQuery({
    queryKey: ["road-stress-summary", id, region],
    enabled: job.data?.status === "completed",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}/summary", {
          signal,
          params: { path: { job_id: id ?? "" }, query: { region } },
        }),
      ),
  })
  const parent = useQuery({
    queryKey: ["road-stress", parentId],
    enabled: Boolean(parentId),
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}", {
          signal,
          params: { path: { job_id: parentId ?? "" } },
        }),
      ),
  })
  const geometry = useQuery({
    queryKey: ["road-stress-geometry", id],
    enabled: id !== null,
    staleTime: Infinity,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}/geometry", {
          signal,
          params: { path: { job_id: id ?? "" } },
        }),
      ),
  })
  const impacts = useQuery({
    queryKey: ["road-stress-impacts", id, region, offset],
    enabled: job.data?.status === "completed",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}/impacts", {
          signal,
          params: { path: { job_id: id ?? "" }, query: { region, offset, limit: 10 } },
        }),
      ),
  })
  const submit = useMutation({
    mutationFn: (body: { way_ids: number[]; parent_id?: string }) =>
      unwrap(api.POST("/api/v1/road-stress-tests", { body })),
  })
  const cancel = useMutation({
    mutationFn: () =>
      unwrap(
        api.DELETE("/api/v1/road-stress-tests/{job_id}", {
          params: { path: { job_id: id ?? "" } },
        }),
      ),
    onSuccess: () => job.refetch(),
  })
  const route = useMutation({
    mutationFn: (body: { origin: string; destination: string }) =>
      unwrap(
        api.POST("/api/v1/road-stress-tests/{job_id}/routes", {
          params: { path: { job_id: id ?? "" } },
          body,
        }),
      ),
  })
  return { job, parent, summary, impacts, submit, cancel, route, geometry }
}
