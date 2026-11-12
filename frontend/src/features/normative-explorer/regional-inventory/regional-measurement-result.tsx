import { type RegionalRunView, useRegionalPoint } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ErrorState, Skeleton, Stat } from "@/shared/ui"
import { FireProfileNote } from "../fire-scenario"
import { NormativePoint } from "../normative-point"
import { NormativeScenario } from "../normative-scenario"
import type { RegionalInventoryContext } from "./context"
import styles from "./regional-measurement-result.module.css"
import { RegionalFacilities, RegionalRows } from "./regional-pages/regional-pages"

type ResultContext = Pick<
  RegionalInventoryContext,
  "selectedPoint" | "onPoint" | "routeStage" | "onRouteStage"
> & { readonly result: RegionalRunView }

export function RegionalMeasurementResult(props: ResultContext) {
  const { result, routeStage, selectedPoint, onPoint } = props
  const { t } = useTranslation()
  const f = useFormatters()
  const walking = result.unit === "metres"
  const known =
    routeStage === "baseline" ? result.baseline_measured_paths : result.scenario_measured_paths
  return (
    <div className={styles.result}>
      <Stat
        label={t("normative:measuredPaths")}
        value={t("normative:measuredPathCount", {
          known: f.integer(known),
          total: f.integer(result.origins),
        })}
      />
      <p>
        {t(
          walking
            ? "normative:regionalWalkingNote"
            : result.mode === "emergency_response"
              ? "normative:regionalFireNote"
              : "normative:regionalPhysicalNote",
        )}
      </p>
      <FireProfileNote profile={result.fire_profile} />
      <p>{t("normative:observed", { date: f.date(result.saved_at) })}</p>
      <NormativeScenario result={result} />
      <PointDetails {...props} />
      <RegionalRows
        key={`${result.run_id}:${routeStage}`}
        view={result}
        stage={routeStage}
        selectedPoint={selectedPoint}
        onPoint={onPoint}
      />
      <RegionalFacilities runId={result.run_id} total={result.facility_count} />
    </div>
  )
}

function PointDetails({ result, selectedPoint, routeStage, onRouteStage }: ResultContext) {
  const query = useRegionalPoint(result.run_id, selectedPoint, routeStage)
  const { t } = useTranslation()
  if (!selectedPoint) return null
  if (query.isPending) return <Skeleton lines={4} />
  if (query.isError)
    return <ErrorState title={t("normative:loadError")} onRetry={() => void query.refetch()} />
  return (
    <NormativePoint
      point={query.data.row}
      walking={result.unit === "metres"}
      fire={result.mode === "emergency_response"}
      regional
      runId={result.run_id}
      stage={routeStage}
      onStage={onRouteStage}
      hasScenario={result.closed_way_ids.length > 0}
      facilityName={query.data.facility?.name}
    />
  )
}
