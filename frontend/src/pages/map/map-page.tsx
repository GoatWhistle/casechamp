import { StressMapLegend } from "@/entities/road-stress"
import { MapChat } from "@/features/map-chat"
import { MapExplorer } from "@/features/map-explorer"
import { NormativePanel } from "@/features/normative-explorer"
import { showStressView, useStressView } from "@/shared/hooks/use-stress-view"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function MapPage() {
  const { t } = useTranslation()
  const stressView = useStressView()
  useDocumentTitle(null)
  return (
    <>
      <h1 className="visually-hidden" tabIndex={-1}>
        {t("map:title")}
      </h1>
      <StressMapLegend />
      <MapExplorer
        renderPanel={({ context, onMapCommand, roads, onChatChange, ...normative }) => {
          const chat = (
            <MapChat
              context={{
                ...context,
                road_way_ids: roads.selected.map((r) => r.way_id),
                stress_job_id: stressView.jobId,
                stress_point_id: stressView.selected?.point.id ?? null,
              }}
              onMapCommand={onMapCommand}
              onCalculation={roads.showCalculation}
              onSessionChange={() => {
                onChatChange()
                showStressView({ jobId: null, impacts: [], route: null })
              }}
            />
          )
          return normative.normativeId ? (
            <NormativePanel
              key={normative.normativeId}
              criterionId={normative.normativeId}
              display={normative.normativeDisplay}
              onDisplay={normative.onNormativeDisplay}
              onRegion={normative.onNormativeRegion}
              regionName={normative.normativeRegionName}
              regionId={normative.normativeRegionId}
              title={normative.metricLabel}
              roads={roads.selected}
              selectedPoint={normative.selectedPoint}
              onPoint={normative.onPoint}
              routeStage={normative.routeStage}
              onRouteStage={normative.onRouteStage}
            >
              {chat}
            </NormativePanel>
          ) : (
            chat
          )
        }}
      />
    </>
  )
}
