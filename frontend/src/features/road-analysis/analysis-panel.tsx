import { useEffect } from "react"
import { useRoadAnalysis } from "@/entities/road-analysis"
import type { AnalysisMode, AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, PanelView, Select, ViewHeader } from "@/shared/ui"
import { AnalysisResults } from "./analysis-results"
import styles from "./road-analysis.module.css"

interface AnalysisPanelProps {
  readonly onDevelop: () => void
  readonly regionId: string | null
  readonly mode: AnalysisMode
  readonly onOverlay: (overlay: AnalysisOverlay | null) => void
  readonly onBack: () => void
}

export function AnalysisPanel({
  regionId,
  mode,
  onOverlay,
  onBack,
  onDevelop,
}: AnalysisPanelProps) {
  const { t } = useTranslation()
  const analysis = useRoadAnalysis(regionId, mode)
  const job = analysis.job
  const title = t(mode === "criticality" ? "graph:tools.criticality" : "graph:tools.improvement")
  useEffect(() => {
    if (analysis.detail.data) onOverlay({ detail: analysis.detail.data, focus: 0 })
  }, [analysis.detail.data, onOverlay])
  return (
    <PanelView
      label={title}
      header={<ViewHeader title={title} backLabel={t("graph:back")} onBack={onBack} />}
      footer={
        <div className={styles.footer}>
          <span className={styles.footerText}>
            {regionId ? t("analysis:waitHint") : t("analysis:pickRegion")}
          </span>
          <Button
            icon="search"
            pending={analysis.start.isPending}
            disabled={mode === "criticality" && (!regionId || analysis.busy)}
            onClick={() => (mode === "criticality" ? analysis.start.mutate(20) : onDevelop())}
          >
            {t("analysis:start")}
          </Button>
        </div>
      }
    >
      <section className={styles.intro}>
        <p className={styles.note}>
          {t(mode === "criticality" ? "analysis:closureSpec" : "traffic:developmentHint")}
        </p>
        {analysis.recent.length ? (
          <Select
            label={t("analysis:history")}
            value={job?.id ?? ""}
            onChange={analysis.selectJob}
            options={analysis.recent.map((j) => ({
              value: j.id,
              label: j.region,
              meta: t(j.mode === "criticality" ? "analysis:criticality" : "analysis:improvement"),
            }))}
          />
        ) : null}
      </section>
      {analysis.error ? (
        <Banner
          tone="danger"
          title={t("analysis:requestError")}
          action={
            <Button variant="secondary" icon="retry" onClick={analysis.retry}>
              {t("analysis:retry")}
            </Button>
          }
        />
      ) : null}
      <AnalysisResults analysis={analysis} onOverlay={onOverlay} />
    </PanelView>
  )
}
