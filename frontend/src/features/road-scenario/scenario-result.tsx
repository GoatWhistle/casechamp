import { type RoadGraphState, ScenarioOutcome, useRoadJobs } from "@/entities/road-graph"
import type { RoadJob } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { EmptyState } from "@/shared/ui"
import { RoadCostNotes } from "./profile/road-cost-notes"
import { RoadJobSpec } from "./road-job-spec"
import { RoadMoney } from "./road-money"

function roadNames(job: RoadJob, roads: RoadGraphState): string[] {
  const known = new Map(
    [...roads.selected, ...(roads.view.data?.segments ?? [])].map((road) => [road.way_id, road]),
  )
  const names = job.changes
    .map((change) => known.get(change.way_id)?.name)
    .filter((name): name is string => Boolean(name))
  return [...new Set(names)]
}

export function ScenarioResult({ roads }: { readonly roads: RoadGraphState }) {
  const { t } = useTranslation()
  const job = roads.job
  const [query] = useRoadJobs(job ? [job.id] : [])
  if (!job || !query) return <EmptyState icon="whatif" title={t("graph:result.empty")} />
  const current = query.data ?? job
  return (
    <>
      <ScenarioOutcome
        query={query}
        detailed
        spec={<RoadJobSpec job={current} names={roadNames(current, roads)} />}
        onCancel={() => roads.cancel.mutate()}
        cancelling={roads.cancel.isPending}
      />
      <RoadCostNotes notes={current.result?.road_cost_notes} />
      {current.appraisal_result ||
      current.addition ||
      current.money_assumptions ||
      current.result?.money ? (
        <RoadMoney job={current} />
      ) : null}
    </>
  )
}
