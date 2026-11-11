import type { StressJob } from "@/shared/api/road-stress"
import { showStressView } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button, Disclosure, Select } from "@/shared/ui"
import { StressImpacts } from "./stress-impacts"
import { StressRoutePanel } from "./stress-route"
import { StressSummary } from "./stress-summary"
import type { useStressTest } from "./use-stress-test"
export function StressResults({
  id,
  job,
  state,
  region,
  offset,
  origin,
  destination,
  setRegion,
  setOffset,
  setOrigin,
  setDestination,
}: {
  readonly id: string | null
  readonly job: StressJob
  readonly state: ReturnType<typeof useStressTest>
  readonly region: string
  readonly offset: number
  readonly origin: string
  readonly destination: string
  readonly setRegion: (v: string) => void
  readonly setOffset: (v: number) => void
  readonly setOrigin: (v: string) => void
  readonly setDestination: (v: string) => void
}) {
  const { t } = useTranslation()
  const regions = (job.regions ?? []).filter((item) => item.settlements > 0)
  const rows = state.impacts.data ?? []
  return (
    <>
      <Select
        label={t("stress:region")}
        value={region}
        onChange={(name) => {
          setRegion(name)
          setOffset(0)
        }}
        options={[
          { value: "", label: t("stress:allRegions") },
          ...regions.map((r) => ({ value: r.name, label: r.name })),
        ]}
      />
      {!state.summary.isError ? <StressSummary summary={state.summary.data} /> : null}
      <Button
        icon="map"
        variant="secondary"
        onClick={() => showStressView({ jobId: id, impacts: [], route: null, regions })}
      >
        {t("stress:overview")}
      </Button>
      {state.parent.data ? (
        <p>
          {t("stress:parentComparison", {
            before: (state.parent.data.regions ?? []).reduce((n, r) => n + r.population, 0),
            after: regions.reduce((n, r) => n + r.population, 0),
            isolationBefore: state.parent.data.newly_isolated_points ?? 0,
            isolationAfter: job.newly_isolated_points ?? 0,
          })}
        </p>
      ) : null}
      {regions.length === 0 ? <p>{t("stress:zero")}</p> : null}
      <StressRoutePanel
        id={id}
        origin={origin}
        destination={destination}
        setOrigin={setOrigin}
        setDestination={setDestination}
        state={state}
      />
      <Disclosure title={t("stress:affectedPlaces")}>
        <StressImpacts
          id={id}
          rows={rows}
          offset={offset}
          setOffset={setOffset}
          setOrigin={setOrigin}
        />
      </Disclosure>
    </>
  )
}
