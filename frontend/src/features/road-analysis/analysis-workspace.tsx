import type { ReactNode } from "react"
import { useScenarioView } from "@/entities/road-graph"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Swap, useInputModality } from "@/shared/motion"
import { AnalysisPanel } from "./analysis-panel"
import styles from "./road-analysis.module.css"

interface AnalysisWorkspaceProps {
  readonly manual: ReactNode
  readonly onDevelop: () => void
  readonly regionId: string | null
  readonly onOverlay: (overlay: AnalysisOverlay | null) => void
}

export function AnalysisWorkspace({
  manual,
  regionId,
  onOverlay,
  onDevelop,
}: AnalysisWorkspaceProps) {
  const { t } = useTranslation()
  const modality = useInputModality()
  const { view, setView } = useScenarioView()
  const analysis = view === "criticality" || view === "improvement" ? view : null
  return (
    <section
      aria-label={t("analysis:title")}
      className={styles.workspace}
      data-instant={modality.instant}
      onKeyDown={modality.onKeyDown}
      onPointerDown={modality.onPointerDown}
    >
      <Swap swapKey={analysis ?? "manual"} as="div" className={styles.screen}>
        {analysis ? (
          <AnalysisPanel
            key={`${regionId}-${analysis}`}
            regionId={regionId}
            onDevelop={onDevelop}
            mode={analysis}
            onOverlay={onOverlay}
            onBack={() => {
              onOverlay(null)
              setView("home")
            }}
          />
        ) : (
          manual
        )}
      </Swap>
    </section>
  )
}
