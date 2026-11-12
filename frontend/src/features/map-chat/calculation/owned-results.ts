import type { ChatEntry } from "@/entities/chat"

export function ownedResults(messages: readonly ChatEntry[], index: number): ChatEntry {
  const message = messages[index]
  if (!message) throw new Error("Missing chat message")
  const previous = messages.slice(0, index)
  const traffic = new Set(previous.flatMap((row) => row.trafficJobs?.map((job) => job.id) ?? []))
  const stress = new Set(previous.flatMap((row) => row.stressTests?.map((job) => job.id) ?? []))
  const analyses = new Set(previous.flatMap((row) => row.analyses?.map((job) => job.id) ?? []))
  const scenarios = new Set(
    previous.flatMap((row) => [
      ...(row.calculations?.flatMap((job) => job.job_ids) ?? []),
      ...(row.scenarios?.flatMap((job) => job.job_ids) ?? []),
    ]),
  )
  return {
    ...message,
    trafficJobs: message.trafficJobs?.filter((job) => !traffic.has(job.id)) ?? [],
    stressTests: message.stressTests?.filter((job) => !stress.has(job.id)) ?? [],
    analyses: message.analyses?.filter((job) => !analyses.has(job.id)) ?? [],
    calculations:
      message.calculations
        ?.map((job) => ({ ...job, job_ids: job.job_ids.filter((id) => !scenarios.has(id)) }))
        .filter((job) => job.job_ids.length) ?? [],
    scenarios:
      message.scenarios
        ?.map((job) => ({ ...job, job_ids: job.job_ids.filter((id) => !scenarios.has(id)) }))
        .filter((job) => job.job_ids.length) ?? [],
  }
}
