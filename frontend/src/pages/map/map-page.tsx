import { useSearchParams } from "react-router"
import { StressCard, StressMapLegend } from "@/entities/road-stress"
import { MapChat } from "@/features/map-chat"
import { MapExplorer } from "@/features/map-explorer"
import { AnalysisWorkspace } from "@/features/road-analysis"
import { RoadScenario } from "@/features/road-scenario"
import { showStressView, useStressView } from "@/shared/hooks/use-stress-view"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function MapPage() {
  const { t } = useTranslation()
  const stressView = useStressView()
  const [params, setParams] = useSearchParams()
  useDocumentTitle(null)
  return (
    <>
      <h1 className="visually-hidden" tabIndex={-1}>
        {t("map:title")}
      </h1>
      <StressMapLegend />
      <MapExplorer
        renderPanel={(summary, context, onMapCommand, roads, onChatChange) => (
          <MapChat
            scenario={
              <AnalysisWorkspace
                regionId={context.region_id ?? null}
                onOverlay={roads.setAnalysisOverlay}
                manual={
                  <RoadScenario
                    roads={roads}
                    context={context}
                    stress={
                      <StressCard
                        jobId={params.get("stress") ?? undefined}
                        onJob={(id) =>
                          setParams(
                            (previous) => {
                              const next = new URLSearchParams(previous)
                              next.set("stress", id)
                              return next
                            },
                            { replace: true },
                          )
                        }
                        selectedWays={roads.selected.map((r) => r.way_id)}
                      />
                    }
                  />
                }
              />
            }
            summary={summary}
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
        )}
      />
    </>
  )
}
