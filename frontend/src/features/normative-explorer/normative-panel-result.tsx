import { memo } from "react"
import type { Assessment } from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import { useTranslation } from "@/shared/i18n"
import { FireProfileNote } from "./fire-scenario"
import styles from "./normative-panel.module.css"
import { NormativePoint } from "./normative-point"
import { NormativePopulation } from "./normative-population"
import { NormativeResultTable } from "./normative-result-table"
import { NormativeScenario } from "./normative-scenario"

export const NormativePanelResult = memo(function NormativePanelResult({
  result,
  selectedPoint,
  onPoint,
  routeStage = "scenario",
  onRouteStage,
}: {
  readonly result: Assessment
  readonly selectedPoint: string | null
  readonly onPoint?: ((id: string, instant?: boolean) => void) | undefined
  readonly routeStage?: NormativeRouteStage | undefined
  readonly onRouteStage?: ((stage: NormativeRouteStage, instant?: boolean) => void) | undefined
}) {
  const { t } = useTranslation()
  const pointRows = routeStage === "baseline" ? result.baseline_rows : result.rows
  const point =
    selectedPoint === null ? undefined : pointRows.find((row) => row.id === selectedPoint)
  return (
    <div className={styles.result}>
      <NormativePopulation result={result} />
      <NormativeScenario result={result} />
      {result.criterion.service === "fire" ? (
        <p>
          {t("normative:savedOriginBasis", {
            basis: t(
              `normative:originBases.${result.origin_basis === "fire_objects" ? "fire_objects" : "settlements"}`,
            ),
          })}
        </p>
      ) : null}
      <FireProfileNote profile={result.fire_profile} />
      {point ? (
        <NormativePoint
          point={point}
          ruleChecks={result.rule_sets?.find((group) => group.id === point.rule_set_id)?.checks}
          walking={result.criterion.mode === "walk"}
          fire={result.criterion.service === "fire"}
          library={result.criterion.service === "library"}
          runId={result.run_id}
          stage={routeStage}
          onStage={onRouteStage}
          hasScenario={result.closed_way_ids.length > 0}
          facilityName={result.facilities.find((item) => item.id === point.facility_id)?.name}
        />
      ) : null}
      <NormativeResultTable
        rows={pointRows}
        objectDestinations={result.origin_basis === "fire_objects"}
        walking={result.criterion.mode === "walk"}
        onPoint={onPoint}
        selectedPoint={selectedPoint}
      />
    </div>
  )
})
