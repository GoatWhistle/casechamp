import { useEffect, useState } from "react"
import { showStressView, updateStressGeometry, useStressView } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button, Card, ErrorState } from "@/shared/ui"
import { StressActions } from "./stress-actions"
import styles from "./stress-card.module.css"
import { StressHistory } from "./stress-history"
import { StressPointDetail } from "./stress-point-detail"
import { StressMethod, StressProgress } from "./stress-progress"
import { StressResults } from "./stress-results"
import { useStressTest } from "./use-stress-test"

export interface StressCardProps {
  readonly onJob?: ((id: string) => void) | undefined
  readonly jobId?: string | undefined
  readonly selectedWays?: readonly number[]
}
export function StressCard({ jobId, selectedWays = [], onJob }: StressCardProps) {
  const { t } = useTranslation()
  const [id, setId] = useState<string | null>(jobId ?? null)
  const [region, setRegion] = useState("")
  const [offset, setOffset] = useState(0)
  const [origin, setOrigin] = useState("")
  const [destination, setDestination] = useState("")
  const view = useStressView()
  const state = useStressTest(id, region, offset)
  useEffect(() => {
    if (view.jobId === id && id && state.geometry.data)
      updateStressGeometry(id, state.geometry.data.lines)
  }, [id, state.geometry.data, view.jobId])
  useEffect(() => {
    if (view.jobId !== id) return
    if (view.selected) setOrigin(view.selected.point.id)
    if (view.selectedRegion) {
      setRegion(view.selectedRegion)
      setOffset(0)
    }
  }, [id, view.jobId, view.selected, view.selectedRegion])
  const job = state.job.data
  const busy = ["queued", "running"].includes(job?.status ?? "")
  const select = (nextId: string) => {
    showStressView({ jobId: nextId, impacts: [], route: null, selected: null, selectedRegion: "" })
    setId(nextId)
    setRegion("")
    setOffset(0)
    setOrigin("")
    setDestination("")
    state.route.reset()
    onJob?.(nextId)
  }
  const launch = (parent: boolean) =>
    state.submit.mutate(submission(selectedWays, id, parent), {
      onSuccess: (next) => select(next.id),
    })
  return (
    <Card
      className={styles.card}
      title={t("stress:title")}
      description={id ? undefined : t("stress:description")}
    >
      <StressActions
        selectedWays={selectedWays}
        id={id}
        pending={state.submit.isPending}
        launch={launch}
      />
      {[
        state.submit,
        state.job,
        state.summary,
        state.impacts,
        state.route,
        state.geometry,
        state.cancel,
      ].some((query) => query.isError) ? (
        <ErrorState
          title={t("stress:error")}
          onRetry={() => {
            void state.job.refetch()
            void state.impacts.refetch()
            void state.geometry.refetch()
            void state.summary.refetch()
          }}
        />
      ) : null}
      {job ? (
        <>
          <StressProgress
            job={job}
            busy={busy}
            pending={state.cancel.isPending}
            cancel={() => state.cancel.mutate()}
          />
          {job.parent_id ? (
            <Button
              icon="arrow-left"
              variant="ghost"
              onClick={() => select(job.parent_id ?? job.id)}
            >
              {t("stress:parent")}
            </Button>
          ) : null}
          {view.jobId === id && view.selected ? <StressPointDetail impact={view.selected} /> : null}
          {job.status === "completed" ? (
            <StressResults
              id={id}
              job={job}
              state={state}
              region={region}
              offset={offset}
              origin={origin}
              destination={destination}
              setRegion={setRegion}
              setOffset={setOffset}
              setOrigin={setOrigin}
              setDestination={setDestination}
            />
          ) : null}
          <StressMethod job={job} />
        </>
      ) : null}
      <StressHistory id={id} select={select} />
    </Card>
  )
}
function submission(ways: readonly number[], id: string | null, parent: boolean) {
  return { way_ids: [...ways], ...(parent && id ? { parent_id: id } : {}) }
}
