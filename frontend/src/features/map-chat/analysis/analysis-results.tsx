import { useEffect, useState } from "react"
import { useAnalysisDetail } from "@/entities/road-analysis"
import type { AnalysisJob, AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button } from "@/shared/ui"
import { AnalysisTable } from "./analysis-table"

interface AnalysisResultsProps {
  readonly job: AnalysisJob
  readonly onOverlay?: ((overlay: AnalysisOverlay) => void) | undefined
}

export function AnalysisResults({ job, onOverlay }: AnalysisResultsProps) {
  const { t } = useTranslation()
  const [selection, setSelection] = useState({
    wayId: null as number | null,
    focus: 0,
    instant: false,
  })
  const detail = useAnalysisDetail(job.id, selection.wayId)
  useEffect(() => {
    if (detail.data && selection.focus)
      onOverlay?.({ detail: detail.data, focus: selection.focus, instant: selection.instant })
  }, [detail.data, selection, onOverlay])
  return (
    <>
      {job.results.length ? (
        <AnalysisTable
          job={job}
          pendingWay={detail.isFetching ? selection.wayId : null}
          onShow={
            onOverlay
              ? (wayId, instant) => setSelection({ wayId, instant, focus: performance.now() })
              : undefined
          }
        />
      ) : (
        <p>{t("analysis:noVerified")}</p>
      )}
      {detail.isError ? (
        <Banner
          tone="danger"
          title={t("analysis:requestError")}
          action={
            <Button icon="retry" onClick={() => detail.refetch()}>
              {t("analysis:retry")}
            </Button>
          }
        />
      ) : null}
    </>
  )
}
