import { MapChat } from "@/features/map-chat"
import { MapExplorer } from "@/features/map-explorer"
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
        renderPanel={({ regionCard, selection, context, onMapCommand, roads, onChatChange }) => (
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
        )}
      />
    </>
  )
}
