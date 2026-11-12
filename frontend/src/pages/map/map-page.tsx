import { MapChat } from "@/features/map-chat"
import { MapExplorer } from "@/features/map-explorer"
import { NormativePanel } from "@/features/normative-explorer"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function MapPage() {
  const { t } = useTranslation()
  useDocumentTitle(null)
  return (
    <>
      <h1 className="visually-hidden" tabIndex={-1}>
        {t("map:title")}
      </h1>
      <MapExplorer
        renderPanel={({
          regionCard,
          selection,
          context,
          onMapCommand,
          roads,
          onChatChange,
          normativeId,
          normativeRegionName,
          normativeRegionId,
          normativeDisplay,
          onNormativeDisplay,
          onNormativeRegion,
          metricLabel,
          selectedPoint,
          onPoint,
          routeStage,
          onRouteStage,
        }) => {
          const chat = (
            <MapChat
              regionCard={regionCard}
              selection={selection}
              context={context}
              roads={roads.selected}
              onClearRoads={roads.clear}
              onMapCommand={onMapCommand}
              onCalculation={roads.showCalculation}
              onScenario={roads.selectJob}
              onAnalysisOverlay={roads.setAnalysisOverlay}
              onSessionChange={onChatChange}
            />
          )
          return normativeId ? (
            <NormativePanel
              key={normativeId}
              onRegion={onNormativeRegion}
              criterionId={normativeId}
              display={normativeDisplay}
              onDisplay={onNormativeDisplay}
              regionName={normativeRegionName}
              regionId={normativeRegionId}
              title={metricLabel}
              roads={roads.selected}
              selectedPoint={selectedPoint}
              onPoint={onPoint}
              routeStage={routeStage}
              onRouteStage={onRouteStage}
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
