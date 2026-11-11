import { useEffect, useState } from "react"
import { useRoadAnalysis } from "@/entities/road-analysis"
import type { AnalysisMode, AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, NumberField, PanelView, Select, ViewHeader } from "@/shared/ui"
import { AnalysisResults } from "./analysis-results"
import styles from "./road-analysis.module.css"

interface AnalysisPanelProps {
  readonly regionId: string | null
  readonly mode: AnalysisMode
  readonly onOverlay: (overlay: AnalysisOverlay | null) => void
  readonly onBack: () => void
}

export function AnalysisPanel({ regionId, mode, onOverlay, onBack }: AnalysisPanelProps) {
  const { t } = useTranslation()
  const [percent, setPercent] = useState("20")
  const analysis = useRoadAnalysis(regionId, mode)
  const amount = Number(percent)
  const valid = Number.isInteger(amount) && amount >= 1 && amount <= 200
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
            disabled={!regionId || !valid || analysis.busy}
            onClick={() => analysis.start.mutate(amount)}
          >
            {t("analysis:start")}
          </Button>
        </div>
      }
    >
      <section className={styles.intro}>
        <p className={styles.note}>
          {t(mode === "criticality" ? "analysis:closureSpec" : "analysis:improvementSpec", {
            percent: amount,
          })}
        </p>
        {mode === "improvement" ? (
          <NumberField
            label={t("analysis:percent")}
            value={percent}
            suffix="%"
            onChange={(e) => setPercent(e.target.value)}
            hint={t("analysis:percentHint")}
            error={valid ? undefined : t("analysis:percentError")}
          />
        ) : null}
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
