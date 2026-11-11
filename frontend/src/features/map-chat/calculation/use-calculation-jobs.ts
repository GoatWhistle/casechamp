import { useQueries } from "@tanstack/react-query"
import type { ChatEntry } from "@/entities/chat"
import { api, unwrap } from "@/shared/api/client"
import type { RoadJob } from "@/shared/api/road-graph"
import type { StressJob } from "@/shared/api/road-stress"

const terminal = (status: string) => ["completed", "failed", "cancelled"].includes(status)

export function useCalculationJobs(message: ChatEntry) {
  const scenarioIds = [
    ...new Set([
      ...(message.calculations?.flatMap((item) => item.job_ids) ?? []),
      ...(message.scenarios?.flatMap((item) => item.job_ids) ?? []),
    ]),
  ]
  const stressIds = [...new Set(message.stressTests?.map((item) => item.id) ?? [])]
  const scenarios = useQueries({
    queries: scenarioIds.map((id) => ({
      queryKey: ["road-scenario", id],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        unwrap(
          api.GET("/api/v1/road-scenarios/{job_id}", {
            signal,
            params: { path: { job_id: id } },
          }),
        ),
      refetchInterval: (query: { state: { data: { status: string } | undefined } }) =>
        terminal(query.state.data?.status ?? "") ? false : 1500,
    })),
  })
  const stress = useQueries({
    queries: stressIds.map((id) => ({
      queryKey: ["road-stress", id],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        unwrap(
          api.GET("/api/v1/road-stress-tests/{job_id}", {
            signal,
            params: { path: { job_id: id } },
          }),
        ),
      refetchInterval: (query: { state: { data: { status: string } | undefined } }) =>
        terminal(query.state.data?.status ?? "") ? false : 1500,
    })),
  })
  const queries = [...scenarios, ...stress]
  const jobs = queries.flatMap((query) => (query.data ? [query.data] : []))
  const finished = jobs.length === queries.length && jobs.every((job) => terminal(job.status))
  const completed = jobs.filter((job) => job.status === "completed").length
  const error = queries.some((query) => query.isError)
  const revision =
    finished && completed > 0 && message.complete && !error
      ? jobs
          .map((job) => `${job.id}:${job.version}:${job.status}`)
          .sort()
          .join(":")
      : null
  const progress = progressOf(jobs, queries.length, stressIds.length > 0)
  return {
    jobs,
    scenarioIds,
    stressIds,
    revision,
    finished,
    completed,
    error,
    ...progress,
    count: queries.length,
    retry: () => {
      for (const query of queries) void query.refetch()
    },
  }
}

function progressOf(jobs: readonly (RoadJob | StressJob)[], count: number, national: boolean) {
  const running = jobs.find((job) => job.status === "running")
  const stage = running && "stage" in running ? running.stage : running ? "routes" : "queued"
  if (!running || (national && count > 1)) return { stage, progress: null }
  if (national)
    return {
      stage,
      progress: Math.min(100, (running.completed / Math.max(1, running.total)) * 100),
    }
  const sum = jobs.reduce(
    (value, job) =>
      value + (terminal(job.status) ? 1 : Math.min(1, job.completed / Math.max(1, job.total))),
    0,
  )
  return { stage, progress: (sum / count) * 100 }
}
