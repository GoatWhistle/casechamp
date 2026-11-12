import {
  useCalculateRegionalMeasurement,
  useRegionalIndexMap,
  useRegionalNormativeCatalog,
  useRegionalRunView,
} from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  Button,
  Card,
  EmptyState,
  ErrorState,
  PanelActions,
  ScrollArea,
  Skeleton,
  Stat,
  StatusBadge,
} from "@/shared/ui"
import { FireScenarioFields, useFireScenario } from "../fire-scenario"
import type { RegionalInventoryContext } from "./context"
import { RegionalIndexCard } from "./regional-index-entry"
import styles from "./regional-inventory.module.css"
import { RegionalMeasurementResult } from "./regional-measurement-result"

function useInventoryState({ regionId, criterionId, roads, display }: RegionalInventoryContext) {
  const latest = useRegionalRunView(regionId ?? "", criterionId, display !== "index")
  const catalog = useRegionalNormativeCatalog(
    regionId ?? "",
    criterionId,
    display !== "index" && latest.data === null,
  )
  const fire = useFireScenario(criterionId === "N03")
  const calculate = useCalculateRegionalMeasurement(regionId ?? "", criterionId, fire.profile)
  return { latest, catalog, fire, calculate, criterionId, closed: roads.map((road) => road.way_id) }
}
type InventoryState = ReturnType<typeof useInventoryState>

export function RegionalInventory(props: RegionalInventoryContext) {
  const state = useInventoryState(props)
  const indexMap = useRegionalIndexMap(props.criterionId, props.routeStage)
  const detailAvailable =
    indexMap.data?.find((row) => row.region_id === props.regionId)?.detail_available !== false
  const { t } = useTranslation()
  return (
    <>
      <ScrollArea className={styles.scroll} label={t("normative:resultRegion")}>
        <div className={styles.details}>
          <RegionalIndexCard
            regionId={props.regionId ?? ""}
            criterionId={props.criterionId}
            stage={props.routeStage}
            runId={state.latest.data?.run_id}
          />
          {props.display === "index" ? (
            props.onDisplay ? (
              <Button
                icon="route"
                variant="secondary"
                disabled={!detailAvailable}
                onClick={() => props.onDisplay?.("travel")}
              >
                {t("normative:indexOpenPaths")}
              </Button>
            ) : null
          ) : (
            <InventoryBody state={state} context={props} />
          )}
        </div>
      </ScrollArea>
      {props.display !== "index" ? <MeasurementAction state={state} /> : null}
    </>
  )
}

function InventoryBody({
  state,
  context,
}: {
  readonly state: InventoryState
  readonly context: RegionalInventoryContext
}) {
  const { latest, calculate, closed } = state
  const { t } = useTranslation()
  if (latest.isPending) return <Skeleton lines={5} />
  if (latest.isError)
    return <ErrorState title={t("normative:loadError")} onRetry={() => void latest.refetch()} />
  return (
    <>
      {context.criterionId === "N01" || context.criterionId === "N02" ? (
        <p>{t("normative:regionalMedicalWarning")}</p>
      ) : null}
      {latest.data ? (
        <RegionalMeasurementResult key={latest.data.run_id} {...context} result={latest.data} />
      ) : (
        <CatalogState state={state} />
      )}
      <FireScenarioFields
        state={state.fire}
        enabled={context.criterionId === "N03"}
        destinationSelection={false}
      />
      {calculate.isError ? (
        <ErrorState
          title={t("normative:calculationError")}
          onRetry={() => calculate.mutate(closed)}
        />
      ) : null}
    </>
  )
}

function CatalogState({ state }: { readonly state: InventoryState }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { catalog } = state
  if (catalog.isPending) return <Skeleton lines={4} />
  if (catalog.isError)
    return <ErrorState title={t("normative:loadError")} onRetry={() => void catalog.refetch()} />
  return (
    <Card
      as="div"
      title={t("normative:regionalInventoryTitle")}
      description={catalog.data.region_name}
    >
      <StatusBadge tone="neutral" label={t("normative:regionalCandidateStatus")} />
      <Stat
        label={t("normative:regionalCandidateCount")}
        value={f.integer(catalog.data.candidate_count)}
      />
      <p>{t("normative:regionalCandidateNote")}</p>
      {!catalog.data.candidate_count ? (
        <EmptyState
          icon="map"
          title={t("normative:regionalInventoryEmpty")}
          description={t("normative:regionalInventoryEmptyHint")}
        />
      ) : null}
    </Card>
  )
}

function MeasurementAction({ state }: { readonly state: InventoryState }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const { catalog, latest, calculate, closed } = state
  const available =
    Boolean(latest.data) ||
    Boolean(
      catalog.data &&
        (catalog.data.road_measurement_available ||
          catalog.data.walking_measurement_available ||
          catalog.data.emergency_measurement_available),
    )
  if (!available) return null
  const count = latest.data?.facility_count ?? catalog.data?.candidate_count ?? 0
  return (
    <PanelActions>
      {closed.length ? (
        <p>{t("normative:selectedRoads", { count: f.integer(closed.length) })}</p>
      ) : null}
      <Button
        icon="route"
        pending={calculate.isPending}
        disabled={count === 0 || calculate.isPending || !state.fire.ready}
        onClick={() => calculate.mutate(closed)}
      >
        {t(closed.length ? "normative:regionalCalculateScenario" : "normative:regionalCalculate")}
      </Button>
    </PanelActions>
  )
}
