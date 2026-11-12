import type { NormativeView } from "@/shared/api/normative-map"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Segmented, StatusBadge } from "@/shared/ui"
import styles from "./normative-symbols.module.css"

export function NormativeSymbols({
  weighted,
  view,
}: {
  readonly weighted: boolean
  readonly view?: NormativeView | undefined
}) {
  const { t } = useTranslation()
  return (
    <div className={styles.symbols}>
      {view ? (
        <Segmented
          label={t("normative:mapDisplay")}
          value={view.display}
          onChange={view.onDisplay}
          options={[
            { value: "index", label: t("normative:indexDisplay") },
            { value: "travel", label: t("normative:travelDisplay") },
            { value: "status", label: t("normative:statusDisplay") },
          ]}
        />
      ) : null}
      <PointSymbols weighted={weighted} view={view} />
      {view?.clustered && view.display !== "index" ? <ClusterSymbols view={view} /> : null}
      {view?.display !== "index" ? (
        <StatusBadge tone="info" icon="office" label={t("normative:mapFacility")} />
      ) : null}
    </div>
  )
}

function PointSymbols({
  weighted,
  view,
}: {
  readonly weighted: boolean
  readonly view: NormativeView | undefined
}) {
  const { t } = useTranslation()
  if (view?.display === "index")
    return <StatusBadge tone="warning" label={t("normative:indexConditional")} />
  if (view && !view.hasResults)
    return <StatusBadge tone="info" icon="office" label={t("normative:regionalCandidateStatus")} />
  if (view?.display === "travel") return <TravelSymbols view={view} />
  return (
    <>
      <p>{t(weighted ? "normative:lowerBound" : "normative:referenceLegend")}</p>
      <StatusBadge tone="success" label={t("normative:mapWithin")} />
      <StatusBadge tone="neutral" label={t("normative:mapUnknown")} />
    </>
  )
}

function TravelSymbols({ view }: { readonly view: NormativeView }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <>
      <p>
        {t(
          view.unit === "metres"
            ? "normative:physicalDistanceLegend"
            : "normative:physicalTimeLegend",
        )}
      </p>
      {view.range ? (
        <>
          <div className={styles.travelRamp} aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <p>
            {t(view.unit === "metres" ? "normative:metreRange" : "normative:minuteRange", {
              min: f.number(view.range[0], 1),
              max: f.number(view.range[1], 1),
            })}
          </p>
        </>
      ) : null}
      <StatusBadge tone="neutral" label={t("normative:physicalPathMissing")} />
    </>
  )
}

function ClusterSymbols({ view }: { readonly view: NormativeView }) {
  const { t } = useTranslation()
  return (
    <>
      <p>{t("normative:mapClusterLegend")}</p>
      {view.viewportReferences === undefined ? null : (
        <p>{t("normative:mapClusterViewport", { count: view.viewportReferences })}</p>
      )}
      {view.mapLoading ? <StatusBadge tone="info" label={t("normative:mapRowsLoading")} /> : null}
      {view.mapError ? (
        <>
          <StatusBadge tone="warning" label={t("normative:mapRowsError")} />
          <Button variant="secondary" icon="retry" onClick={view.onMapRetry}>
            {t("common:action.retry")}
          </Button>
        </>
      ) : null}
    </>
  )
}
