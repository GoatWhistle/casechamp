import { type ReactNode, useState } from "react"
import {
  type Criterion,
  useLatestNormativeAssessment,
  useNormativeAssessment,
  useNormativeCriteria,
  useNormativeFacilities,
  useNormativeFireDestinations,
} from "@/entities/normative"
import type { NormativeDisplay, NormativeRouteStage } from "@/shared/api/normative-map"
import type { RoadSegment } from "@/shared/api/road-graph"
import { useErrorText, useFormatters, useTranslation } from "@/shared/i18n"
import {
  Button,
  Card,
  EmptyState,
  ErrorState,
  PanelActions,
  ScrollArea,
  Segmented,
  Skeleton,
  StatusBadge,
} from "@/shared/ui"
import { FireScenarioFields, useFireScenario } from "./fire-scenario"
import { IndexOverview } from "./index-overview/index-overview"
import { NormativeCoverage } from "./normative-coverage"
import { NormativeFacilities } from "./normative-facilities"
import styles from "./normative-panel.module.css"
import { NormativePanelResult } from "./normative-panel-result"
import { NormativeSource } from "./normative-source"
import {
  canCalculate,
  pilotScopeEnabled,
  showRegionalInventory,
} from "./regional-inventory/pilot-scope"
import { RegionalInventory } from "./regional-inventory/regional-inventory"

export interface NormativePanelProps {
  readonly display?: NormativeDisplay
  readonly onDisplay?: ((display: NormativeDisplay) => void) | undefined
  readonly onRegion?: ((id: string) => void) | undefined
  readonly regionId?: string | null
  readonly regionName?: string | null
  readonly criterionId: string
  readonly title: string
  readonly roads: readonly RoadSegment[]
  readonly selectedPoint: string | null
  readonly onPoint: (id: string, instant?: boolean) => void
  readonly routeStage: NormativeRouteStage
  readonly onRouteStage: (stage: NormativeRouteStage, instant?: boolean) => void
  readonly children: ReactNode
}

export function NormativePanel(props: NormativePanelProps) {
  const { t } = useTranslation()
  const [tab, setTab] = useState("result")
  return (
    <section className={styles.panel} aria-label={t("normative:panelTitle")}>
      <div className={styles.switcher}>
        <Segmented
          value={tab}
          onChange={setTab}
          label={t("normative:panelTitle")}
          options={[
            { value: "result", label: t("normative:resultTab"), icon: "overview" },
            { value: "chat", label: t("normative:chatTab"), icon: "chat" },
          ]}
        />
      </div>
      {tab === "chat" ? (
        <div className={styles.chat}>{props.children}</div>
      ) : (
        <NormativePanelBody {...props} />
      )}
    </section>
  )
}

function NormativePanelBody({
  criterionId,
  regionName,
  regionId,
  title,
  roads,
  selectedPoint,
  onPoint,
  routeStage,
  onRouteStage,
  onRegion,
  display,
  onDisplay,
}: NormativePanelProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const errorText = useErrorText()
  const catalog = useNormativeCriteria()
  const criterion = catalog.data?.find((item) => item.id === criterionId)
  const pilotEnabled = pilotScopeEnabled(regionName, criterion, regionId)
  const latest = useLatestNormativeAssessment(criterionId, pilotEnabled)
  const facilities = useNormativeFacilities(criterionId, pilotEnabled)
  const calculate = useNormativeAssessment()
  const fire = useFireScenario(criterionId === "N03")
  const fireObjects = useNormativeFireDestinations(criterionId === "N03")
  const fireReady = fireScenarioReady(criterionId, fire, fireObjects)
  const command = {
    criterion_id: criterionId,
    closed_way_ids: roads.map((road) => road.way_id),
    ...fire.parameters,
  }
  if (!regionId)
    return <IndexOverview criterionId={criterionId} stage={routeStage} onRegion={onRegion} />
  if (showRegionalInventory(display, regionName, criterion))
    return (
      <RegionalInventory
        key={`${regionId}:${criterionId}`}
        regionId={regionId}
        display={display}
        onDisplay={onDisplay}
        criterionId={criterionId}
        roads={roads}
        selectedPoint={selectedPoint}
        onPoint={onPoint}
        routeStage={routeStage}
        onRouteStage={onRouteStage}
      />
    )
  const result = latest.data
  const supported = canCalculate(criterion, facilities.data)
  const visibleFacilities = result?.facilities ?? facilities.data
  return (
    <>
      <ScrollArea className={styles.scroll} label={t("normative:resultRegion")}>
        <Card as="div" title={title} className={styles.intro} description={criterion?.territory}>
          <StatusBadge tone="neutral" label={t("normative:modeled")} />
          <NormativeCoverage result={result} />
        </Card>
        <div className={styles.details}>
          <FireScenarioFields
            state={fire}
            enabled={criterionId === "N03"}
            objectCount={fireObjects.data?.length}
            objectPending={fireObjects.isPending}
            objectError={fireObjects.isError}
            onRetryObjects={() => {
              void fireObjects.refetch()
            }}
          />
          {[catalog, latest, facilities].some((query) => query.isError) ? (
            <ErrorState
              title={t("normative:loadError")}
              onRetry={() => {
                void catalog.refetch()
                void latest.refetch()
                void facilities.refetch()
              }}
            />
          ) : null}
          {[catalog, latest].some((query) => query.isPending) ? <Skeleton lines={4} /> : null}
          {calculate.isError ? (
            <ErrorState
              title={t("normative:calculationError")}
              description={errorText(calculate.error)}
              onRetry={() => calculate.mutate(command)}
            />
          ) : null}
          {calculate.isPending ? (
            <StatusBadge tone="neutral" icon="loader" label={t("normative:pendingTitle")} />
          ) : null}
          {result ? (
            <NormativePanelResult
              result={result}
              selectedPoint={selectedPoint}
              onPoint={onPoint}
              routeStage={routeStage}
              onRouteStage={onRouteStage}
            />
          ) : !catalog.isPending && !latest.isPending && !facilities.isPending ? (
            <NormativeEmpty criterion={criterion} supported={supported} />
          ) : null}
          <NormativeSource criterion={criterion} result={result} />
          {visibleFacilities ? <NormativeFacilities facilities={visibleFacilities} /> : null}
          <p className={styles.explanation}>{t("normative:catalogNote")}</p>
        </div>
      </ScrollArea>
      <PanelActions>
        {roads.length ? (
          <p>{t("normative:selectedRoads", { count: f.integer(roads.length) })}</p>
        ) : null}
        <Button
          icon="scenario"
          pending={calculate.isPending}
          disabled={!supported || !fireReady || calculate.isPending}
          onClick={() => calculate.mutate(command)}
        >
          {t(roads.length ? "normative:scenarioRun" : "normative:baseRun")}
        </Button>
      </PanelActions>
    </>
  )
}

function emptyResultKey(criterion: Criterion | undefined, supported: boolean) {
  if (supported) return "normative:noResult"
  return criterion?.mode === "car" ? "normative:emptyFacilities" : "normative:unsupported"
}

function NormativeEmpty({
  criterion,
  supported,
}: {
  readonly criterion: Criterion | undefined
  readonly supported: boolean
}) {
  const { t } = useTranslation()
  if (criterion?.mode === "walk" && supported)
    return (
      <EmptyState
        icon="map"
        title={t("normative:walkingReady")}
        description={t("normative:walkingExplanation")}
      />
    )
  if (criterion && ["N03", "N04", "N07", "N09"].includes(criterion.id)) {
    const id = criterion.id as "N03" | "N04" | "N07" | "N09"
    return (
      <EmptyState
        icon="info"
        title={t(`normative:unavailable.${id}.title`)}
        description={t(`normative:unavailable.${id}.description`)}
      />
    )
  }
  return <EmptyState icon="overview" title={t(emptyResultKey(criterion, supported))} />
}

function fireScenarioReady(
  criterionId: string,
  state: ReturnType<typeof useFireScenario>,
  objects: ReturnType<typeof useNormativeFireDestinations>,
) {
  if (criterionId !== "N03") return true
  if (!state.ready) return false
  return (
    state.originBasis !== "fire_objects" ||
    (!objects.isPending && !objects.isError && (objects.data?.length ?? 0) > 0)
  )
}
